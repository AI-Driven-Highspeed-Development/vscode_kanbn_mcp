"""
Constants for VSCode Kanbn MCP.

Defines tag sets, default options, and column configurations.
"""

from typing import Any


# --- Default Board Options ---

DEFAULT_INDEX_OPTIONS: dict[str, Any] = {
    "hiddenColumns": ["Archive"],
    "startedColumns": ["In Progress"],
    "completedColumns": ["Done"],
    "defaultTaskWorkload": 2,
    "taskWorkloadTags": {
        "Nothing": 0,
        "Tiny": 1,
        "Small": 2,
        "Medium": 3,
        "Large": 5,
        "Huge": 8,
    },
}

DEFAULT_COLUMNS: list[str] = ["Backlog", "In Progress", "Done", "Archive"]


# --- Tag Sets ---

WORK_TYPE_TAGS: set[str] = {
    "feature", "bug", "chore", "refactor", "testing", "documentation",
    "research", "design", "planning", "spike"
}

DOMAIN_TAGS: set[str] = {
    "frontend", "backend", "database", "api", "infrastructure", "ci-cd",
    "security", "performance", "accessibility", "ui-ux", "algorithm",
    "devtools", "config", "logging"
}

MANAGEMENT_TAGS: set[str] = {
    "communication", "training", "review", "devops", "maintenance",
    "meta", "support"
}

PRIORITY_TAGS: set[str] = {
    "urgent", "high-priority", "medium-priority", "low-priority",
    "not-planned", "blocked"
}

WORKLOAD_TAGS: dict[str, int] = {
    "Nothing": 0, "Tiny": 1, "Small": 2, "Medium": 3, "Large": 5, "Huge": 8
}

ALL_VALID_TAGS: set[str] = (
    WORK_TYPE_TAGS | DOMAIN_TAGS | MANAGEMENT_TAGS | PRIORITY_TAGS | set(WORKLOAD_TAGS.keys())
)
