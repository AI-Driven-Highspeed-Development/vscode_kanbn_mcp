"""
Data models for VSCode Kanbn MCP.

Provides KanbnBoard and KanbnTask classes for managing board state and task files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from utils.logger_util import Logger

from mcps.vscode_kanbn_mcp.constants import DEFAULT_COLUMNS, DEFAULT_INDEX_OPTIONS
from mcps.vscode_kanbn_mcp.helpers import (
    build_frontmatter,
    ensure_workload_tag,
    now_iso,
    parse_frontmatter,
    validate_tags,
)

log = Logger(name="KanbnMCP", verbose=False)


class KanbnBoard:
    """Represents a kanbn board with index and tasks."""
    
    def __init__(self, kanbn_path: str | Path):
        """Initialize board at the given .kanbn path."""
        self.kanbn_path = Path(kanbn_path)
        self.index_path = self.kanbn_path / "index.md"
        self.tasks_path = self.kanbn_path / "tasks"
        
        self._options: dict[str, Any] = {}
        self._name: str = ""
        self._description: str = ""
        self._columns: dict[str, list[str]] = {}  # column_name -> list of task IDs
    
    @property
    def exists(self) -> bool:
        """Check if the board exists."""
        return self.index_path.exists()
    
    def load(self) -> None:
        """Load board state from index.md."""
        if not self.exists:
            raise FileNotFoundError(f"Board not found at {self.kanbn_path}")
        
        content = self.index_path.read_text(encoding="utf-8")
        self._options, body = parse_frontmatter(content)
        
        self._columns = {}
        current_column = None
        
        for line in body.split("\n"):
            line_stripped = line.strip()
            
            # Level-1 heading = project name
            if line_stripped.startswith("# ") and not line_stripped.startswith("## "):
                self._name = line_stripped[2:].strip()
                continue
            
            # Level-2 heading = column
            if line_stripped.startswith("## "):
                current_column = line_stripped[3:].strip()
                self._columns[current_column] = []
                continue
            
            # Task link: - [task-id](tasks/task-id.md)
            if current_column and line_stripped.startswith("- ["):
                match = re.match(r"- \[([^\]]+)\]\(tasks/([^)]+)\.md\)", line_stripped)
                if match:
                    task_id = match.group(2)
                    self._columns[current_column].append(task_id)
                continue
            
            # Description (before first column)
            if not current_column and line_stripped and not line_stripped.startswith("#"):
                if self._description:
                    self._description += "\n" + line_stripped
                else:
                    self._description = line_stripped
    
    def save(self) -> None:
        """Save board state to index.md."""
        self.kanbn_path.mkdir(parents=True, exist_ok=True)
        self.tasks_path.mkdir(parents=True, exist_ok=True)
        
        lines = []
        
        # Frontmatter
        if self._options:
            lines.append(build_frontmatter(self._options).rstrip("\n"))
            lines.append("")
        
        # Project name
        lines.append(f"# {self._name}")
        lines.append("")
        
        # Description
        if self._description:
            lines.append(self._description)
            lines.append("")
        
        # Columns
        for column, task_ids in self._columns.items():
            lines.append(f"## {column}")
            lines.append("")
            for task_id in task_ids:
                lines.append(f"- [{task_id}](tasks/{task_id}.md)")
            lines.append("")
        
        content = "\n".join(lines)
        self.index_path.write_text(content, encoding="utf-8")
        log.info(f"Saved board index: {self.index_path}")
    
    def create(
        self,
        name: str,
        description: str = "",
        columns: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> None:
        """Create a new board."""
        if self.exists:
            raise FileExistsError(f"Board already exists at {self.kanbn_path}")
        
        self._name = name
        self._description = description
        self._options = {**DEFAULT_INDEX_OPTIONS, **(options or {})}
        self._columns = {col: [] for col in (columns or DEFAULT_COLUMNS)}
        self.save()
    
    def get_columns(self) -> list[str]:
        """Return list of column names."""
        return list(self._columns.keys())
    
    def get_tasks_in_column(self, column: str) -> list[str]:
        """Return list of task IDs in a column."""
        return self._columns.get(column, [])
    
    def add_task_to_column(self, task_id: str, column: str) -> None:
        """Add a task ID to a column."""
        if column not in self._columns:
            self._columns[column] = []
        if task_id not in self._columns[column]:
            self._columns[column].append(task_id)
    
    def remove_task_from_column(self, task_id: str, column: str) -> bool:
        """Remove a task ID from a column. Returns True if removed."""
        if column in self._columns and task_id in self._columns[column]:
            self._columns[column].remove(task_id)
            return True
        return False
    
    def find_task_column(self, task_id: str) -> str | None:
        """Find which column a task is in."""
        for column, tasks in self._columns.items():
            if task_id in tasks:
                return column
        return None
    
    def move_task(self, task_id: str, target_column: str) -> str | None:
        """Move a task to a different column. Returns previous column or None."""
        if target_column not in self._columns:
            raise ValueError(f"Column '{target_column}' does not exist")
        
        current = self.find_task_column(task_id)
        if current:
            self.remove_task_from_column(task_id, current)
        self.add_task_to_column(task_id, target_column)
        return current
    
    def reorder_tasks(self, column: str, task_ids: list[str]) -> list[str]:
        """Reorder tasks within a column.
        
        Args:
            column: The column to reorder tasks in
            task_ids: Ordered list of task IDs (must match existing tasks in column)
        
        Returns:
            The previous order of task IDs
        
        Raises:
            ValueError: If column doesn't exist or task_ids don't match
        """
        if column not in self._columns:
            raise ValueError(f"Column '{column}' does not exist")
        
        current_tasks = set(self._columns[column])
        new_tasks = set(task_ids)
        
        if current_tasks != new_tasks:
            missing = current_tasks - new_tasks
            extra = new_tasks - current_tasks
            errors = []
            if missing:
                errors.append(f"Missing tasks: {missing}")
            if extra:
                errors.append(f"Unknown tasks: {extra}")
            raise ValueError("; ".join(errors))
        
        previous_order = self._columns[column].copy()
        self._columns[column] = task_ids
        return previous_order


class KanbnTask:
    """Represents a kanbn task."""
    
    def __init__(self, tasks_path: str | Path, task_id: str):
        """Initialize task with path and ID."""
        self.tasks_path = Path(tasks_path)
        self.task_id = task_id
        self.file_path = self.tasks_path / f"{task_id}.md"
        
        self._metadata: dict[str, Any] = {}
        self._name: str = ""
        self._description: str = ""
        self._subtasks: list[dict[str, Any]] = []  # {"text": str, "completed": bool}
        self._relations: list[str] = []
        self._comments: list[dict[str, Any]] = []
    
    @property
    def exists(self) -> bool:
        """Check if the task file exists."""
        return self.file_path.exists()
    
    def load(self) -> None:
        """Load task from file."""
        if not self.exists:
            raise FileNotFoundError(f"Task not found: {self.file_path}")
        
        content = self.file_path.read_text(encoding="utf-8")
        self._metadata, body = parse_frontmatter(content)
        
        current_section = None
        description_lines = []
        
        for line in body.split("\n"):
            stripped = line.strip()
            
            # Level-1 heading = task name
            if stripped.startswith("# ") and not stripped.startswith("## "):
                self._name = stripped[2:].strip()
                current_section = "description"
                continue
            
            # Level-2 heading = section
            if stripped.startswith("## "):
                section_name = stripped[3:].strip().lower()
                if section_name == "sub-tasks":
                    current_section = "subtasks"
                elif section_name == "relations":
                    current_section = "relations"
                elif section_name == "comments":
                    current_section = "comments"
                else:
                    current_section = "description"
                continue
            
            # Parse content based on current section
            if current_section == "description":
                description_lines.append(line)
            elif current_section == "subtasks" and stripped.startswith("- ["):
                # Handle both lowercase [x] and uppercase [X] for completed tasks
                completed = stripped.startswith("- [x]") or stripped.startswith("- [X]")
                text = re.sub(r"^- \[[xX ]\]\s*", "", stripped)
                self._subtasks.append({"text": text, "completed": completed})
            elif current_section == "relations" and stripped.startswith("- ["):
                self._relations.append(stripped)
            elif current_section == "comments" and stripped.startswith("- author:"):
                self._comments.append({"raw": stripped})
        
        self._description = "\n".join(description_lines).strip()
    
    def save(self) -> None:
        """Save task to file."""
        self.tasks_path.mkdir(parents=True, exist_ok=True)
        
        lines = []
        
        # Frontmatter
        if self._metadata:
            lines.append(build_frontmatter(self._metadata).rstrip("\n"))
            lines.append("")
        
        # Task name
        lines.append(f"# {self._name}")
        lines.append("")
        
        # Description
        if self._description:
            lines.append(self._description)
            lines.append("")
        
        # Sub-tasks (only if present)
        if self._subtasks:
            lines.append("## Sub-tasks")
            lines.append("")
            for st in self._subtasks:
                marker = "[x]" if st.get("completed") else "[ ]"
                lines.append(f"- {marker} {st['text']}")
            lines.append("")
        
        # Relations (only if present)
        if self._relations:
            lines.append("## Relations")
            lines.append("")
            for rel in self._relations:
                lines.append(rel)
            lines.append("")
        
        # Comments (only if present)
        if self._comments:
            lines.append("## Comments")
            lines.append("")
            for comment in self._comments:
                if "raw" in comment:
                    lines.append(comment["raw"])
                else:
                    lines.append(f"- author: \"{comment.get('author', 'Unknown')}\"")
                    lines.append(f"  date: {comment.get('date', now_iso())}")
                    lines.append(f"  {comment.get('text', '')}")
            lines.append("")
        
        content = "\n".join(lines)
        self.file_path.write_text(content, encoding="utf-8")
        log.info(f"Saved task: {self.file_path}")
    
    def create(
        self,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        assigned: str | None = None,
        due: str | None = None,
        started: str | None = None,
        completed: str | None = None,
        subtasks: list[str] | None = None,
    ) -> None:
        """Create a new task."""
        if self.exists:
            raise FileExistsError(f"Task already exists: {self.file_path}")
        
        now = now_iso()
        
        raw_tags = tags or []
        valid_tags, invalid_tags = validate_tags(raw_tags)
        if invalid_tags:
            log.warning(f"Invalid tags ignored: {invalid_tags}")
        valid_tags = ensure_workload_tag(valid_tags)
        
        self._name = name
        self._description = description
        self._metadata = {
            "created": now,
            "updated": now,
            "progress": 0.0,
            "tags": valid_tags,
        }
        
        if assigned:
            self._metadata["assigned"] = assigned
        if due:
            self._metadata["due"] = due
        if started:
            self._metadata["started"] = started
        if completed:
            self._metadata["completed"] = completed
            self._metadata["progress"] = 1.0  # Auto-set progress when completed
        
        self._subtasks = [{"text": st, "completed": False} for st in (subtasks or [])]
        self.save()
    
    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        assigned: str | None = None,
        due: str | None = None,
        progress: float | None = None,
        started: str | None = None,
        completed: str | None = None,
        subtasks: list[dict[str, Any]] | None = None,
    ) -> None:
        """Update an existing task."""
        if not self.exists:
            raise FileNotFoundError(f"Task not found: {self.file_path}")
        
        self.load()
        
        if name is not None:
            self._name = name
        if description is not None:
            self._description = description
        if tags is not None:
            valid_tags, invalid_tags = validate_tags(tags)
            if invalid_tags:
                log.warning(f"Invalid tags ignored: {invalid_tags}")
            self._metadata["tags"] = ensure_workload_tag(valid_tags)
        if assigned is not None:
            self._metadata["assigned"] = assigned
        if due is not None:
            self._metadata["due"] = due
        if progress is not None:
            self._metadata["progress"] = max(0.0, min(1.0, progress))
        if started is not None:
            self._metadata["started"] = started
        if completed is not None:
            self._metadata["completed"] = completed
        if subtasks is not None:
            self._subtasks = subtasks
        
        self._metadata["updated"] = now_iso()
        self.save()
    
    def delete(self) -> None:
        """Delete the task file."""
        if self.exists:
            self.file_path.unlink()
            log.info(f"Deleted task: {self.file_path}")
    
    def to_dict(self) -> dict[str, Any]:
        """Return task as dictionary."""
        return {
            "id": self.task_id,
            "name": self._name,
            "description": self._description,
            "metadata": self._metadata,
            "subtasks": self._subtasks,
            "relations": self._relations,
            "comments": self._comments,
        }
