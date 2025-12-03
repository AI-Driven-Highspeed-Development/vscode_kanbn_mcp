"""
VSCode Kanbn MCP Server - FastMCP-based MCP server for kanbn board management.

This module provides the MCP server entry point using the FastMCP pattern.
Run with: python -m mcps.vscode_kanbn_mcp.server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcps.vscode_kanbn_mcp.kanbn_controller import KanbnController

# Create MCP server instance
mcp = FastMCP(
    name="kanbn",
    instructions=(
        "Kanbn board management MCP server. "
        "Use these tools to create and manage kanbn-compatible planning boards "
        "that work with the vscode-kanbn extension."
    ),
)

# Module-level MCP instance for tool functions
_kanbn: KanbnController | None = None


def _get_kanbn() -> KanbnController:
    """Get or create the KanbnController instance."""
    global _kanbn
    if _kanbn is None:
        _kanbn = KanbnController()
    return _kanbn


def set_workspace_root(workspace_root: str) -> None:
    """Set the workspace root for the MCP server."""
    global _kanbn
    _kanbn = KanbnController(workspace_root=workspace_root)


# --- Board Tools ---


@mcp.tool()
def init_board(
    name: str,
    description: str = "",
    columns: list[str] | None = None,
    kanbn_path: str | None = None,
) -> dict:
    """Initialize a new kanbn board.
    
    Creates a .kanbn directory with index.md and tasks folder.
    
    Args:
        name: The name of the board
        description: Optional description for the board
        columns: List of column names. Defaults to ["Backlog", "In Progress", "Done", "Archive"]
        kanbn_path: Optional custom path for the .kanbn directory
    
    Returns:
        dict with success status, path, and column information
    """
    return _get_kanbn().init_board(
        name=name,
        description=description,
        columns=columns,
        kanbn_path=kanbn_path,
    )


@mcp.tool()
def get_board_status(kanbn_path: str | None = None) -> dict:
    """Get the current status of a kanbn board.
    
    Returns all columns with their task counts and task IDs.
    
    Args:
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with board name, description, and column information
    """
    return _get_kanbn().get_board_status(kanbn_path=kanbn_path)


# --- Task Tools ---


@mcp.tool()
def add_task(
    name: str,
    description: str = "",
    column: str = "Backlog",
    tags: list[str] | None = None,
    assigned: str | None = None,
    due: str | None = None,
    subtasks: list[str] | None = None,
    kanbn_path: str | None = None,
) -> dict:
    """Add a new task to the kanbn board.
    
    Creates a task file in .kanbn/tasks/ and adds a reference to the column.
    
    Args:
        name: The task name (will be converted to kebab-case ID)
        description: Task description/body text
        column: Column to add the task to. Defaults to "Backlog"
        tags: List of tags. Valid tags include work_type (feature, bugfix, etc.),
              domain (frontend, backend, etc.), priority (Critical, High, etc.),
              workload (Tiny, Small, Medium, Large, Huge). Defaults to ["Small"] if none.
        assigned: Person assigned to the task
        due: Due date in ISO format (YYYY-MM-DD)
        subtasks: List of subtask descriptions
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with success status, task_id, column, and file_path
    """
    return _get_kanbn().add_task(
        name=name,
        description=description,
        column=column,
        tags=tags,
        assigned=assigned,
        due=due,
        subtasks=subtasks,
        kanbn_path=kanbn_path,
    )


@mcp.tool()
def move_task(
    task_id: str,
    target_column: str,
    kanbn_path: str | None = None,
) -> dict:
    """Move a task to a different column.
    
    Also applies column behaviors:
    - Moving to startedColumns sets the 'started' date
    - Moving to completedColumns sets 'completed' date and progress=1.0
    
    Args:
        task_id: The task ID (kebab-case)
        target_column: The column to move the task to
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with success status, from_column, and to_column
    """
    return _get_kanbn().move_task(
        task_id=task_id,
        target_column=target_column,
        kanbn_path=kanbn_path,
    )


@mcp.tool()
def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    assigned: str | None = None,
    due: str | None = None,
    progress: float | None = None,
    subtasks: list[dict] | None = None,
    kanbn_path: str | None = None,
) -> dict:
    """Update an existing task.
    
    Only provided fields will be updated; others remain unchanged.
    
    Args:
        task_id: The task ID to update
        name: New task name
        description: New description
        tags: New list of tags (replaces existing)
        assigned: New assignee
        due: New due date
        progress: New progress value (0.0 to 1.0)
        subtasks: New subtasks list. Each item is a dict with 'text' and optional 'completed'
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with success status and file_path
    """
    return _get_kanbn().update_task(
        task_id=task_id,
        name=name,
        description=description,
        tags=tags,
        assigned=assigned,
        due=due,
        progress=progress,
        subtasks=subtasks,
        kanbn_path=kanbn_path,
    )


@mcp.tool()
def get_task(task_id: str, kanbn_path: str | None = None) -> dict:
    """Get details of a specific task.
    
    Args:
        task_id: The task ID to retrieve
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with task details including metadata, subtasks, and current column
    """
    return _get_kanbn().get_task(task_id=task_id, kanbn_path=kanbn_path)


@mcp.tool()
def delete_task(task_id: str, kanbn_path: str | None = None) -> dict:
    """Delete a task from the board.
    
    Removes the task file and its reference from the index.
    
    Args:
        task_id: The task ID to delete
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with success status and the column it was removed from
    """
    return _get_kanbn().delete_task(task_id=task_id, kanbn_path=kanbn_path)


# --- Column Tools ---


@mcp.tool()
def add_column(
    column_name: str,
    position: int | None = None,
    kanbn_path: str | None = None,
) -> dict:
    """Add a new column to the board.
    
    Args:
        column_name: Name of the new column
        position: Optional position index (0-based). Defaults to end of list.
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with success status and updated column list
    """
    return _get_kanbn().add_column(
        column_name=column_name,
        position=position,
        kanbn_path=kanbn_path,
    )


# --- Utility Tools ---


@mcp.tool()
def list_valid_tags() -> dict:
    """List all valid tags organized by category.
    
    Returns:
        dict with tag categories: work_type, domain, management, priority, workload
    """
    return _get_kanbn().list_valid_tags()


@mcp.tool()
def batch_add_tasks(
    tasks: list[dict],
    default_column: str = "Backlog",
    kanbn_path: str | None = None,
) -> dict:
    """Add multiple tasks at once.
    
    Each task dict can have: name (required), description, column, tags, assigned, due, subtasks.
    
    Args:
        tasks: List of task specifications
        default_column: Default column for tasks without a column specified
        kanbn_path: Optional path to the .kanbn directory
    
    Returns:
        dict with created tasks, failed tasks, and counts
    """
    return _get_kanbn().batch_add_tasks(
        tasks=tasks,
        default_column=default_column,
        kanbn_path=kanbn_path,
    )


# --- Entry Point ---


def main() -> None:
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
