"""Role-based access control — design doc §7.2.4.

Static permission matrix per role. The API layer reads `currentUser.role`
from a Firebase-Auth custom claim and gates each endpoint with
`require(role, permission)`.

Imported by:
- `core/govern/__init__.py` re-exports
- `api/deps.py` (forthcoming) — endpoint gating
- `api/audits.py`, `api/recourse.py` — fine-grained checks
- tests in `backend/tests/unit/test_rbac.py` (forthcoming)
"""

from __future__ import annotations

from typing import Literal

Role = Literal["admin", "analyst", "reviewer", "viewer"]

Permission = Literal[
    "audit.create",
    "audit.view",
    "audit.delete",
    "audit.signoff",
    "remediation.apply",
    "remediation.approve",
    "user.manage",
    "policy.manage",
    "recourse.file",
    "recourse.review",
    "report.generate",
    "report.view",
]


PERMISSIONS: dict[Role, frozenset[Permission]] = {
    "admin": frozenset(
        {
            "audit.create",
            "audit.view",
            "audit.delete",
            "audit.signoff",
            "remediation.apply",
            "remediation.approve",
            "user.manage",
            "policy.manage",
            "recourse.file",
            "recourse.review",
            "report.generate",
            "report.view",
        }
    ),
    "analyst": frozenset(
        {
            "audit.create",
            "audit.view",
            "remediation.apply",
            "report.generate",
            "report.view",
            "recourse.file",
        }
    ),
    "reviewer": frozenset(
        {
            "audit.view",
            "audit.signoff",
            "remediation.approve",
            "recourse.review",
            "report.view",
        }
    ),
    "viewer": frozenset(
        {
            "audit.view",
            "report.view",
        }
    ),
}


def can(role: Role, permission: Permission) -> bool:
    """Return True iff `role` is allowed to perform `permission`."""
    return permission in PERMISSIONS.get(role, frozenset())


def require(role: Role, permission: Permission) -> None:
    """Raise `PermissionError` if `role` is not allowed to perform `permission`."""
    if not can(role, permission):
        raise PermissionError(f"Role '{role}' is not permitted to perform '{permission}'.")


__all__ = ["PERMISSIONS", "Permission", "Role", "can", "require"]
