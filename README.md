# VSCode Kanbn MCP

## Overview
MCP (Model Context Protocol) module for managing kanbn-compatible planning boards. Provides AI agents with reliable, consistent tools to create and modify kanbn boards that work with the [vscode-kanbn](https://github.com/samgiz/vscode-kanbn) extension and [kanbn CLI](https://github.com/basementuniverse/kanbn).

The MCP ensures strict adherence to the kanbn format specification, handling:
- YAML frontmatter for board options and task metadata
- Proper markdown structure for index and task files
- Tag validation against predefined categories
- Automatic date handling for started/completed columns

## Features
- **Board Initialization**: Create new kanbn boards with customizable columns and options.
- **Task Management**: Add, update, move, and delete tasks with full metadata support.
- **Batch Operations**: Add multiple tasks in a single call.
- **Tag Validation**: Validates tags against predefined work type, domain, priority, and workload categories.
- **Column Auto-Behavior**: Automatically sets `started`/`completed` dates when moving tasks to configured columns.
- **Format Compliance**: Ensures all generated files are compatible with kanbn tooling.
- **MCP Protocol**: Proper MCP server implementation with FastMCP for AI agent integration.

## Running as MCP Server

The module provides a proper MCP server that can be run via stdio transport:

```bash
# Run the server directly
python -m mcps.vscode_kanbn_mcp.server

# Or from the project root
cd /path/to/adhd_framework
python -m mcps.vscode_kanbn_mcp.server
```

### MCP Client Configuration

For VS Code or other MCP clients, add to your MCP configuration:

```json
{
  "mcpServers": {
    "kanbn": {
      "command": "python",
      "args": ["-m", "mcps.vscode_kanbn_mcp.server"],
      "cwd": "/path/to/adhd_framework"
    }
  }
}
```

## Usage as Library

```python
from mcps.vscode_kanbn_mcp import KanbnMCP, get_kanbn_mcp

# Initialize MCP for a workspace
mcp = get_kanbn_mcp(workspace_root="/path/to/project")

# Create a new board
mcp.init_board(
    name="My Project",
    description="Project planning board",
    columns=["Backlog", "In Progress", "Review", "Done", "Archive"]
)

# Add a task
mcp.add_task(
    name="Implement authentication",
    description="Add OAuth2 authentication flow",
    column="Backlog",
    tags=["feature", "security", "Large"],
    subtasks=["Research OAuth providers", "Implement flow", "Add tests"]
)

# Move task to In Progress
mcp.move_task("implement-authentication", "In Progress")

# Get board status
status = mcp.get_board_status()
print(status["columns"])  # Shows all columns with task counts

# Update task progress
mcp.update_task("implement-authentication", progress=0.5)

# Batch add tasks
mcp.batch_add_tasks([
    {"name": "Write docs", "tags": ["documentation", "Small"]},
    {"name": "Fix bug #123", "column": "In Progress", "tags": ["bug", "Tiny"]},
])
```

## Module Structure
```
vscode_kanbn_mcp/
├── __init__.py                      # Package exports
├── constants.py                     # Tag sets and default options
├── helpers.py                       # Utility functions (kebab-case, YAML parsing)
├── models.py                        # KanbnBoard and KanbnTask classes
├── kanbn_mcp.py                     # Main MCP class (library API)
├── server.py                        # FastMCP server entry point
├── vscode_kanbn_mcp.instructions.md # AI agent instructions
├── init.yaml                        # ADHD module config
├── .config_template                 # Config template
└── README.md                        # This file
```

## MCP Tools Reference

The server exposes these tools via MCP protocol:

| Tool | Description |
|------|-------------|
| `init_board` | Create a new kanbn board |
| `get_board_status` | Get board info with columns and task counts |
| `add_task` | Add a task to the board |
| `move_task` | Move task between columns |
| `update_task` | Update task properties |
| `get_task` | Get full task details |
| `delete_task` | Remove task from board |
| `add_column` | Add a new column |
| `list_valid_tags` | Get all valid tags by category |
| `batch_add_tasks` | Add multiple tasks at once |

## Library API Reference

### `KanbnMCP`

| Method | Description |
|--------|-------------|
| `init_board(name, description, columns, kanbn_path)` | Create a new kanbn board |
| `get_board_status(kanbn_path)` | Get board info with columns and task counts |
| `add_task(name, description, column, tags, ...)` | Add a task to the board |
| `move_task(task_id, target_column, kanbn_path)` | Move task between columns |
| `update_task(task_id, name, description, ...)` | Update task properties |
| `get_task(task_id, kanbn_path)` | Get full task details |
| `delete_task(task_id, kanbn_path)` | Remove task from board |
| `add_column(column_name, position, kanbn_path)` | Add a new column |
| `list_valid_tags()` | Get all valid tags by category |
| `batch_add_tasks(tasks, default_column, kanbn_path)` | Add multiple tasks at once |

### Valid Tags

| Category | Tags |
|----------|------|
| Work Type | feature, bug, chore, refactor, testing, documentation, research, design, planning, spike |
| Domain | frontend, backend, database, api, infrastructure, ci-cd, security, performance, accessibility, ui-ux, algorithm, devtools, config, logging |
| Management | communication, training, review, devops, maintenance, meta, support |
| Priority | urgent, high-priority, medium-priority, low-priority, not-planned, blocked |
| Workload | Nothing (0), Tiny (1), Small (2), Medium (3), Large (5), Huge (8) |

## Dependencies

- `mcp[cli]>=1.9.0` - MCP Python SDK with CLI support

## See Also
- [kanbn CLI Documentation](https://github.com/basementuniverse/kanbn)
- [vscode-kanbn Extension](https://github.com/samgiz/vscode-kanbn)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Instruction Core (syncs instructions to `.github/`)