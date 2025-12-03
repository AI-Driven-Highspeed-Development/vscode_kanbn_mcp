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
    
    Matches kanbn library's paramCase() behavior:
    - Converts spaces and underscores to hyphens
    - Removes special characters
    - Collapses multiple hyphens
    """
    text = text.lower().strip()
    # First convert underscores and spaces to hyphens (before removing special chars)
    text = re.sub(r"[\s_]+", "-", text)
    # Remove special characters except hyphens and alphanumerics
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


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
