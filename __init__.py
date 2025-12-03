"""
VSCode Kanbn MCP - Model Context Protocol for kanbn board management.

Provides tools for AI agents to create and manage kanbn-compatible
planning boards for the vscode-kanbn extension.

Usage as MCP Server:
    python -m mcps.vscode_kanbn_mcp.server

Usage as Library:
    from mcps.vscode_kanbn_mcp import KanbnMCP, get_kanbn_mcp
    mcp = get_kanbn_mcp(workspace_root="/path/to/project")
    result = mcp.add_task(name="My Task", column="Backlog")
"""

# Add path handling to work from the new nested directory structure
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()  # Use current working directory as project root
sys.path.insert(0, project_root)

from mcps.vscode_kanbn_mcp.constants import (
    ALL_VALID_TAGS,
    DOMAIN_TAGS,
    MANAGEMENT_TAGS,
    PRIORITY_TAGS,
    WORK_TYPE_TAGS,
    WORKLOAD_TAGS,
)
from mcps.vscode_kanbn_mcp.kanbn_controller import KanbnController, get_kanbn_mcp
from mcps.vscode_kanbn_mcp.models import KanbnBoard, KanbnTask

__all__ = [
    "KanbnController",
    "KanbnBoard",
    "KanbnTask",
    "get_kanbn_mcp",
    "WORK_TYPE_TAGS",
    "DOMAIN_TAGS",
    "MANAGEMENT_TAGS",
    "PRIORITY_TAGS",
    "WORKLOAD_TAGS",
    "ALL_VALID_TAGS",
]
