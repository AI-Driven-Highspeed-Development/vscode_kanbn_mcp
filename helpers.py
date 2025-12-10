"""
Helper functions for VSCode Kanbn MCP.

Provides utilities for kebab-case conversion, YAML frontmatter parsing,
tag validation, and ISO timestamp generation.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import yaml

from mcps.vscode_kanbn_mcp.constants import ALL_VALID_TAGS, WORKLOAD_TAGS


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case for filenames and task IDs.
    
    Matches kanbn library's paramCase() behavior exactly:
    1. Insert hyphen before uppercase letters in camelCase (FastAPI → Fast-API)
    2. Lowercase everything
    3. Split on special characters (space, underscore, punctuation, etc.)
    4. Join with hyphens
    5. Remove leading/trailing hyphens
    
    Examples:
        "Setup FastAPI Project" → "setup-fast-api-project"
        "SQLAlchemy" → "sqlalchemy"
        "Add workspace_core tests" → "add-workspace-core-tests"
    """
    # Step 1: Insert hyphen before capitals in camelCase sequences
    # This regex matches: one or more uppercase letters followed by any char
    # The replacement adds a hyphen before the match (except at start)
    text = re.sub(
        r"([A-Z]+(.?))",
        lambda m: (("-" if m.start() > 0 else "") + m.group(0)).lower(),
        text
    )
    
    # Step 2: Split on special characters and whitespace, join with hyphens
    # Matches the kanbn special char set: space, punctuation, symbols
    parts = re.split(r"[\s!?.,@:;|\\\/\"'`£$%^&*{}\[\]()<>~#+\-=_¬]+", text)
    
    # Step 3: Filter empty parts and join
    result = "-".join(p for p in parts if p)
    
    # Step 4: Remove leading/trailing hyphens
    return result.strip("-")


def now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.
    
    Returns (frontmatter_dict, body_content).
    """
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}
    
    body = parts[2].lstrip("\n")
    return frontmatter, body


def build_frontmatter(data: dict[str, Any]) -> str:
    """Build YAML frontmatter string from dict."""
    if not data:
        return ""
    yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n"


def validate_tags(tags: list[str]) -> tuple[list[str], list[str]]:
    """Validate tags against known tag sets.
    
    Returns (valid_tags, invalid_tags).
    """
    valid = []
    invalid = []
    for tag in tags:
        if tag in ALL_VALID_TAGS:
            valid.append(tag)
        else:
            invalid.append(tag)
    return valid, invalid


def ensure_workload_tag(tags: list[str]) -> list[str]:
    """Ensure at least one workload tag exists, default to 'Small'."""
    workload_set = set(WORKLOAD_TAGS.keys())
    if not any(t in workload_set for t in tags):
        tags = tags + ["Small"]
    return tags


# --- Mermaid Gantt Chart Helpers ---

# Characters that break Mermaid Gantt syntax
MERMAID_UNSAFE_CHARS = [':', ';', '#', '"', "'", '`', '(', ')', '[', ']', '{', '}', '\n', '\r']


def to_mermaid_id(task_id: str) -> str:
    """Convert task_id to Mermaid-safe ID (alphanumeric + underscore only)."""
    return task_id.replace("-", "_")


def sanitize_mermaid_title(title: str, max_length: int = 40) -> str:
    """Sanitize task title for Mermaid Gantt chart.
    
    - Removes unsafe characters
    - Truncates to max_length
    - Ensures non-empty result
    """
    result = title
    for char in MERMAID_UNSAFE_CHARS:
        result = result.replace(char, " ")
    # Collapse multiple spaces
    result = " ".join(result.split())
    # Truncate
    if len(result) > max_length:
        result = result[:max_length - 3].rstrip() + "..."
    # Ensure non-empty
    if not result.strip():
        result = "Task"
    return result


def parse_iso_date(value: str | datetime | None) -> str | None:
    """Extract YYYY-MM-DD from ISO 8601 datetime string or datetime object.
    
    Handles both string ISO dates and datetime objects (from YAML parsing).
    Returns None if input is None or unparseable.
    """
    if value is None:
        return None
    
    # Handle datetime objects (YAML auto-parses ISO dates)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    
    # Handle strings
    if not isinstance(value, str) or len(value) < 10:
        return None
    
    # Handle both "2024-01-01T00:00:00.000Z" and "2024-01-01" formats
    try:
        date_part = value[:10]
        # Validate it's actually a date
        datetime.strptime(date_part, "%Y-%m-%d")
        return date_part
    except (TypeError, ValueError):
        return None


def add_days_to_date(date_str: str, days: int = 1) -> str:
    """Add days to a YYYY-MM-DD date string."""
    from datetime import datetime, timedelta
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt += timedelta(days=days)
    return dt.strftime("%Y-%m-%d")
