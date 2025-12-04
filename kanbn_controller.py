"""
VSCode Kanbn MCP - Model Context Protocol for managing kanbn boards.

Provides tools for creating and managing kanbn-compatible planning boards
that work with the vscode-kanbn extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.logger_util import Logger

from mcps.vscode_kanbn_mcp.constants import (
    DOMAIN_TAGS,
    MANAGEMENT_TAGS,
    PRIORITY_TAGS,
    WORK_TYPE_TAGS,
    WORKLOAD_TAGS,
)
from mcps.vscode_kanbn_mcp.helpers import now_iso, to_kebab_case
from mcps.vscode_kanbn_mcp.models import KanbnBoard, KanbnTask

log = Logger(name="KanbnController", verbose=False)


class KanbnController:
    """
    MCP interface for managing kanbn boards.
    
    Provides high-level operations for AI agents to create and manage
    kanbn-compatible planning boards.
    """
    
    def __init__(self, workspace_root: str | Path | None = None):
        """Initialize MCP with optional workspace root."""
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
    
    def _get_board(self, kanbn_path: str | None = None) -> KanbnBoard:
        """Get a board instance."""
        path = Path(kanbn_path) if kanbn_path else self.workspace_root / ".kanbn"
        return KanbnBoard(path)
    
    def _get_task(self, board: KanbnBoard, task_id: str) -> KanbnTask:
        """Get a task instance."""
        return KanbnTask(board.tasks_path, task_id)
    
    # --- Board Operations ---
    
    def init_board(
        self,
        name: str,
        description: str = "",
        columns: list[str] | None = None,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Initialize a new kanbn board."""
        board = self._get_board(kanbn_path)
        
        if board.exists:
            return {"success": False, "error": f"Board already exists at {board.kanbn_path}"}
        
        try:
            board.create(name=name, description=description, columns=columns)
            return {
                "success": True,
                "path": str(board.kanbn_path),
                "index_path": str(board.index_path),
                "columns": board.get_columns(),
            }
        except Exception as e:
            log.error(f"Failed to create board: {e}")
            return {"success": False, "error": str(e)}
    
    def get_board_status(self, kanbn_path: str | None = None) -> dict[str, Any]:
        """Get current board status including all columns and task counts."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": f"Board not found at {board.kanbn_path}"}
        
        try:
            board.load()
            columns_info = {}
            for col in board.get_columns():
                task_ids = board.get_tasks_in_column(col)
                columns_info[col] = {"count": len(task_ids), "tasks": task_ids}
            
            return {
                "success": True,
                "path": str(board.kanbn_path),
                "name": board._name,
                "description": board._description,
                "columns": columns_info,
            }
        except Exception as e:
            log.error(f"Failed to read board: {e}")
            return {"success": False, "error": str(e)}
    
    # --- Task Operations ---
    
    def add_task(
        self,
        name: str,
        description: str = "",
        column: str = "Backlog",
        tags: list[str] | None = None,
        assigned: str | None = None,
        due: str | None = None,
        subtasks: list[str] | None = None,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Add a new task to the board."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": f"Board not found. Run init_board first."}
        
        try:
            board.load()
            
            if column not in board.get_columns():
                return {"success": False, "error": f"Column '{column}' not found."}
            
            task_id = to_kebab_case(name)
            task = self._get_task(board, task_id)
            
            if task.exists:
                return {"success": False, "error": f"Task '{task_id}' already exists."}
            
            task.create(
                name=name, description=description, tags=tags,
                assigned=assigned, due=due, subtasks=subtasks,
            )
            
            board.add_task_to_column(task_id, column)
            self._apply_column_behavior(board, task, column)
            board.save()
            
            return {
                "success": True,
                "task_id": task_id,
                "column": column,
                "file_path": str(task.file_path),
            }
        except Exception as e:
            log.error(f"Failed to add task: {e}")
            return {"success": False, "error": str(e)}
    
    def move_task(
        self,
        task_id: str,
        target_column: str,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Move a task to a different column."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            
            if target_column not in board.get_columns():
                return {"success": False, "error": f"Column '{target_column}' not found."}
            
            previous_column = board.move_task(task_id, target_column)
            
            task = self._get_task(board, task_id)
            if task.exists:
                task.load()
                task._metadata["updated"] = now_iso()
                self._apply_column_behavior(board, task, target_column, update_only=True)
                task.save()
            
            board.save()
            
            return {
                "success": True,
                "task_id": task_id,
                "from_column": previous_column,
                "to_column": target_column,
            }
        except Exception as e:
            log.error(f"Failed to move task: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_column_behavior(
        self,
        board: KanbnBoard,
        task: KanbnTask,
        column: str,
        update_only: bool = False,
    ) -> None:
        """Apply started/completed column behaviors to a task."""
        needs_save = False
        
        if column in board._options.get("startedColumns", []):
            if "started" not in task._metadata:
                task._metadata["started"] = now_iso()
                needs_save = True
        
        if column in board._options.get("completedColumns", []):
            task._metadata["completed"] = now_iso()
            task._metadata["progress"] = 1.0
            needs_save = True
        
        if needs_save and not update_only:
            task.save()
    
    def update_task(
        self,
        task_id: str,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        assigned: str | None = None,
        due: str | None = None,
        progress: float | None = None,
        subtasks: list[dict[str, Any]] | None = None,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing task. If name changes, file is renamed and index updated."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            task = self._get_task(board, task_id)
            
            if not task.exists:
                return {"success": False, "error": f"Task '{task_id}' not found."}
            
            # Check if name change requires file rename
            new_task_id = task_id
            if name is not None:
                new_task_id = to_kebab_case(name)
                if new_task_id != task_id:
                    # Check if new ID already exists
                    new_task = self._get_task(board, new_task_id)
                    if new_task.exists:
                        return {
                            "success": False,
                            "error": f"Cannot rename: task '{new_task_id}' already exists.",
                        }
            
            # Update task content
            task.update(
                name=name, description=description, tags=tags,
                assigned=assigned, due=due, progress=progress, subtasks=subtasks,
            )
            
            # If name changed, rename file and update board index
            if new_task_id != task_id:
                new_file_path = board.tasks_path / f"{new_task_id}.md"
                task.file_path.rename(new_file_path)
                
                # Update board index
                column = board.find_task_column(task_id)
                if column:
                    board.remove_task_from_column(task_id, column)
                    board.add_task_to_column(new_task_id, column)
                    board.save()
                
                return {
                    "success": True,
                    "task_id": new_task_id,
                    "previous_task_id": task_id,
                    "file_path": str(new_file_path),
                    "renamed": True,
                }
            
            return {"success": True, "task_id": task_id, "file_path": str(task.file_path)}
        except Exception as e:
            log.error(f"Failed to update task: {e}")
            return {"success": False, "error": str(e)}
    
    def get_task(
        self,
        task_id: str | None = None,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Get task details. If task_id is None, returns all tasks."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            
            # If no task_id provided, return all tasks
            if task_id is None:
                return self._get_all_tasks(board)
            
            task = self._get_task(board, task_id)
            
            if not task.exists:
                return {"success": False, "error": f"Task '{task_id}' not found."}
            
            task.load()
            column = board.find_task_column(task_id)
            
            return {"success": True, "column": column, **task.to_dict()}
        except Exception as e:
            log.error(f"Failed to get task: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_all_tasks(self, board: KanbnBoard) -> dict[str, Any]:
        """Get all tasks from the board organized by column."""
        tasks_by_column: dict[str, list[dict[str, Any]]] = {}
        all_tasks: list[dict[str, Any]] = []
        
        for column in board.get_columns():
            task_ids = board.get_tasks_in_column(column)
            tasks_by_column[column] = []
            
            for tid in task_ids:
                task = self._get_task(board, tid)
                if task.exists:
                    task.load()
                    task_data = {"column": column, **task.to_dict()}
                    tasks_by_column[column].append(task_data)
                    all_tasks.append(task_data)
        
        return {
            "success": True,
            "total_count": len(all_tasks),
            "tasks": all_tasks,
            "by_column": tasks_by_column,
        }
    
    def delete_task(self, task_id: str, kanbn_path: str | None = None) -> dict[str, Any]:
        """Delete a task from the board."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            task = self._get_task(board, task_id)
            
            column = board.find_task_column(task_id)
            if column:
                board.remove_task_from_column(task_id, column)
                board.save()
            
            if task.exists:
                task.delete()
            
            return {"success": True, "task_id": task_id, "removed_from": column}
        except Exception as e:
            log.error(f"Failed to delete task: {e}")
            return {"success": False, "error": str(e)}
    
    def add_column(
        self,
        column_name: str,
        position: int | None = None,
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Add a new column to the board."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            
            if column_name in board._columns:
                return {"success": False, "error": f"Column '{column_name}' already exists."}
            
            if position is not None:
                items = list(board._columns.items())
                items.insert(position, (column_name, []))
                board._columns = dict(items)
            else:
                board._columns[column_name] = []
            
            board.save()
            
            return {"success": True, "column": column_name, "columns": board.get_columns()}
        except Exception as e:
            log.error(f"Failed to add column: {e}")
            return {"success": False, "error": str(e)}
    
    def list_valid_tags(self) -> dict[str, Any]:
        """List all valid tags organized by category."""
        return {
            "success": True,
            "work_type": sorted(WORK_TYPE_TAGS),
            "domain": sorted(DOMAIN_TAGS),
            "management": sorted(MANAGEMENT_TAGS),
            "priority": sorted(PRIORITY_TAGS),
            "workload": WORKLOAD_TAGS,
        }
    
    def batch_add_tasks(
        self,
        tasks: list[dict[str, Any]],
        default_column: str = "Backlog",
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Add multiple tasks at once."""
        results: dict[str, Any] = {"success": True, "created": [], "failed": []}
        
        for task_spec in tasks:
            name = task_spec.get("name")
            if not name:
                results["failed"].append({"error": "Missing name", "spec": task_spec})
                continue
            
            result = self.add_task(
                name=name,
                description=task_spec.get("description", ""),
                column=task_spec.get("column", default_column),
                tags=task_spec.get("tags"),
                assigned=task_spec.get("assigned"),
                due=task_spec.get("due"),
                subtasks=task_spec.get("subtasks"),
                kanbn_path=kanbn_path,
            )
            
            if result.get("success"):
                results["created"].append(result)
            else:
                results["failed"].append({**result, "name": name})
        
        results["created_count"] = len(results["created"])
        results["failed_count"] = len(results["failed"])
        results["success"] = results["failed_count"] == 0
        
        return results
    
    def reorder_tasks(
        self,
        column: str,
        task_ids: list[str],
        kanbn_path: str | None = None,
    ) -> dict[str, Any]:
        """Reorder tasks within a column."""
        board = self._get_board(kanbn_path)
        
        if not board.exists:
            return {"success": False, "error": "Board not found"}
        
        try:
            board.load()
            
            if column not in board.get_columns():
                return {"success": False, "error": f"Column '{column}' not found."}
            
            previous_order = board.reorder_tasks(column, task_ids)
            board.save()
            
            return {
                "success": True,
                "column": column,
                "previous_order": previous_order,
                "new_order": task_ids,
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            log.error(f"Failed to reorder tasks: {e}")
            return {"success": False, "error": str(e)}


# --- Module-level convenience instance ---

_mcp_instance: KanbnController | None = None


def get_kanbn_mcp(workspace_root: str | Path | None = None) -> KanbnController:
    """Get or create the KanbnMCP instance."""
    global _mcp_instance
    if _mcp_instance is None or workspace_root is not None:
        _mcp_instance = KanbnController(workspace_root)
    return _mcp_instance
