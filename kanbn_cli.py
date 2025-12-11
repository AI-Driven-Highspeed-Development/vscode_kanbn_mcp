"""CLI commands and registration for vscode_kanbn_mcp.

Exposes Kanbn MCP tools as CLI commands for command-line usage.
"""

from __future__ import annotations

import argparse
import json

from mcps.vscode_kanbn_mcp.kanbn_controller import KanbnController
from managers.cli_manager import CLIManager, ModuleRegistration, Command, CommandArg


# ─────────────────────────────────────────────────────────────────────────────
# Controller Access
# ─────────────────────────────────────────────────────────────────────────────

_controller: KanbnController | None = None


def _get_controller() -> KanbnController:
    """Get or create the controller instance."""
    global _controller
    if _controller is None:
        _controller = KanbnController()
    return _controller


def _print_result(result: dict) -> int:
    """Print result as JSON and return exit code."""
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("success", True) else 1


# ─────────────────────────────────────────────────────────────────────────────
# Handler Functions
# ─────────────────────────────────────────────────────────────────────────────

def init_board_cmd(args: argparse.Namespace) -> int:
    """Initialize a new kanbn board."""
    columns = args.columns.split(",") if args.columns else None
    result = _get_controller().init_board(
        name=args.name,
        description=args.description or "",
        columns=columns,
        kanbn_path=args.path,
    )
    return _print_result(result)


def get_status_cmd(args: argparse.Namespace) -> int:
    """Get board status."""
    result = _get_controller().get_board_status(kanbn_path=args.path)
    return _print_result(result)


def add_task_cmd(args: argparse.Namespace) -> int:
    """Add a new task."""
    tags = args.tags.split(",") if args.tags else None
    result = _get_controller().add_task(
        name=args.name,
        description=args.description or "",
        column=args.column or "Backlog",
        tags=tags,
        assigned=args.assigned,
        due=args.due,
        kanbn_path=args.path,
    )
    return _print_result(result)


def move_task_cmd(args: argparse.Namespace) -> int:
    """Move a task to a different column."""
    result = _get_controller().move_task(
        task_id=args.task_id,
        target_column=args.column,
        kanbn_path=args.path,
    )
    return _print_result(result)


def update_task_cmd(args: argparse.Namespace) -> int:
    """Update an existing task."""
    tags = args.tags.split(",") if args.tags else None
    result = _get_controller().update_task(
        task_id=args.task_id,
        name=args.name,
        description=args.description,
        tags=tags,
        assigned=args.assigned,
        due=args.due,
        progress=args.progress,
        kanbn_path=args.path,
    )
    return _print_result(result)


def get_task_cmd(args: argparse.Namespace) -> int:
    """Get task details."""
    result = _get_controller().get_task(task_id=args.task_id, kanbn_path=args.path)
    return _print_result(result)


def delete_task_cmd(args: argparse.Namespace) -> int:
    """Delete a task."""
    result = _get_controller().delete_task(task_id=args.task_id, kanbn_path=args.path)
    return _print_result(result)


def add_column_cmd(args: argparse.Namespace) -> int:
    """Add a new column."""
    result = _get_controller().add_column(
        column_name=args.name,
        position=args.position,
        kanbn_path=args.path,
    )
    return _print_result(result)


def list_tags_cmd(args: argparse.Namespace) -> int:
    """List valid tags."""
    result = _get_controller().list_valid_tags()
    return _print_result(result)


def gantt_cmd(args: argparse.Namespace) -> int:
    """Generate Gantt chart."""
    result = _get_controller().generate_gantt_chart(kanbn_path=args.path)
    return _print_result(result)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Registration
# ─────────────────────────────────────────────────────────────────────────────

def register_cli() -> None:
    """Register vscode_kanbn_mcp commands with CLIManager."""
    cli = CLIManager()
    cli.register_module(ModuleRegistration(
        module_name="vscode_kanbn_mcp",
        short_name="kb",
        description="Kanbn board management CLI",
        commands=[
            Command(
                name="init",
                help="Initialize a new kanbn board",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:init_board_cmd",
                args=[
                    CommandArg(name="name", help="Board name"),
                    CommandArg(name="--description", short="-d", help="Board description"),
                    CommandArg(name="--columns", short="-c", help="Comma-separated column names"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="status",
                help="Get board status",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:get_status_cmd",
                args=[
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="add",
                help="Add a new task",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:add_task_cmd",
                args=[
                    CommandArg(name="name", help="Task name"),
                    CommandArg(name="--description", short="-d", help="Task description"),
                    CommandArg(name="--column", short="-c", help="Target column", default="Backlog"),
                    CommandArg(name="--tags", short="-t", help="Comma-separated tags"),
                    CommandArg(name="--assigned", short="-a", help="Assignee"),
                    CommandArg(name="--due", help="Due date (YYYY-MM-DD)"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="move",
                help="Move a task to a different column",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:move_task_cmd",
                args=[
                    CommandArg(name="task_id", help="Task ID"),
                    CommandArg(name="column", help="Target column"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="update",
                help="Update an existing task",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:update_task_cmd",
                args=[
                    CommandArg(name="task_id", help="Task ID"),
                    CommandArg(name="--name", short="-n", help="New task name"),
                    CommandArg(name="--description", short="-d", help="New description"),
                    CommandArg(name="--tags", short="-t", help="Comma-separated tags"),
                    CommandArg(name="--assigned", short="-a", help="Assignee"),
                    CommandArg(name="--due", help="Due date (YYYY-MM-DD)"),
                    CommandArg(name="--progress", type="float", help="Progress (0.0-1.0)"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="get",
                help="Get task details (or all tasks if no ID)",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:get_task_cmd",
                args=[
                    CommandArg(name="--task-id", short="-t", help="Task ID (omit for all)"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="delete",
                help="Delete a task",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:delete_task_cmd",
                args=[
                    CommandArg(name="task_id", help="Task ID"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="add-column",
                help="Add a new column to the board",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:add_column_cmd",
                args=[
                    CommandArg(name="name", help="Column name"),
                    CommandArg(name="--position", short="-i", type="int", help="Position index"),
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
            Command(
                name="tags",
                help="List valid tags",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:list_tags_cmd",
            ),
            Command(
                name="gantt",
                help="Generate Gantt chart",
                handler="mcps.vscode_kanbn_mcp.kanbn_cli:gantt_cmd",
                args=[
                    CommandArg(name="--path", short="-p", help="Custom .kanbn path"),
                ],
            ),
        ],
    ))
