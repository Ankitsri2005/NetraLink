from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    ANALYST = "analyst"
    AUDITOR = "auditor"


PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"read", "write", "delete", "export", "manage_users"},
    Role.INVESTIGATOR: {"read", "write", "export"},
    Role.ANALYST: {"read", "write"},
    Role.AUDITOR: {"read", "audit"},
}


def has_permission(role: str | Role, action: str) -> bool:
    """Check if a given role is allowed to perform the action."""
    try:
        r = Role(role)
    except ValueError:
        return False
    return action in PERMISSIONS.get(r, set())
