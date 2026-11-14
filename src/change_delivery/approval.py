"""Approval must pin plan_sha256; mismatch never opens a Draft PR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class ApprovalError(ValueError):
    pass


@dataclass(frozen=True)
class Approval:
    plan_sha256: str
    approver: str
    approved_at: str
    allow_external_write: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_sha256": self.plan_sha256,
            "approver": self.approver,
            "approved_at": self.approved_at,
            "allow_external_write": self.allow_external_write,
        }


def parse_approval(raw: Mapping[str, Any]) -> Approval:
    digest = str(raw.get("plan_sha256") or "").strip()
    if not digest:
        raise ApprovalError("approval.plan_sha256 is required")
    approver = str(raw.get("approver") or "").strip()
    if not approver:
        raise ApprovalError("approval.approver is required")
    approved_at = str(raw.get("approved_at") or "").strip()
    if not approved_at:
        raise ApprovalError("approval.approved_at is required")
    allow = bool(raw.get("allow_external_write", False))
    return Approval(
        plan_sha256=digest,
        approver=approver,
        approved_at=approved_at,
        allow_external_write=allow,
    )


def assert_plan_bound(approval: Approval, plan_sha256: str) -> None:
    if approval.plan_sha256 != plan_sha256:
        raise ApprovalError(
            "approval.plan_sha256 does not match current plan; "
            "re-run shadow and re-approve (cannot open Draft PR with stale approval)"
        )
