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
