"""P1 pipeline: Issue → shadow → approval(plan_sha256) → Draft PR (mock)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from change_delivery.actor import (
    ActorAuthorizationError,
    CaseActor,
    actor_from_trust_headers,
    reject_body_actor,
)
from change_delivery.approval import Approval, ApprovalError, assert_plan_bound, parse_approval
from change_delivery.plan import DeliveryPlan, build_plan, load_issue
from change_delivery.trajectory import build_format_b_trajectory, validate_format_b_shape


@dataclass(frozen=True)
class RunResult:
    ok: bool
    mode: str
    report_path: Path
    trajectory_path: Path
    draft_path: Path | None
    error: str | None
    report: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _shadow_steps(plan: DeliveryPlan) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "thought": "Read issue and freeze delivery plan fingerprint",
            "tool_calls": [
                {
                    "name": "read_issue",
                    "arguments": {"issue_id": plan.issue_id},
                }
            ],
            "observation": f"plan_sha256={plan.plan_sha256}",
        },
        {
            "step": 2,
            "thought": "Shadow execute intended paths without writing source or GitHub",
            "tool_calls": [
                {
                    "name": "shadow_apply",
                    "arguments": {
                        "paths": list(plan.intended_paths),
                        "external_write": False,
                    },
                }
            ],
            "observation": "shadow ok; no push; no create_pull_request",
        },
    ]


def run_shadow(
    *,
    issue_path: Path | str,
    artifact_dir: Path | str,
    headers: Mapping[str, str] | None = None,
    body: Mapping[str, object] | None = None,
) -> RunResult:
    reject_body_actor(body)
    actor = actor_from_trust_headers(headers)
    issue = load_issue(issue_path)
    plan = build_plan(issue)
    run_id = f"shadow-{uuid4().hex[:10]}"
    out = Path(artifact_dir) / run_id
    traj = build_format_b_trajectory(
        query=f"Deliver issue {plan.issue_id}: {plan.title}",
        final_answer=f"shadow complete; plan_sha256={plan.plan_sha256}",
        steps=_shadow_steps(plan),
        task_episode_id=plan.issue_id,
        acceptance_criteria=list(plan.acceptance_criteria),
        session_id=run_id,
    )
    shape_errors = validate_format_b_shape(traj)
    if shape_errors:
        raise RuntimeError(f"Format B shape invalid: {shape_errors}")

    report = {
        "schema": "change-delivery-report/v1",
        "mode": "shadow",
        "run_id": run_id,
        "ok": True,
        "actor": {"actor_id": actor.actor_id, "source": actor.source},
        "plan": plan.to_dict(),
        "plan_sha256": plan.plan_sha256,
        "issue_path": str(issue_path),
        "external_writes": [],
        "draft_pr": None,
        "created_at": _utc_now(),
        "format_b": {"compatible": True, "missing_fields": []},
    }
    report_path = out / "report.json"
    traj_path = out / "trajectory.format-b.json"
    _write_json(report_path, report)
    _write_json(traj_path, traj)
    return RunResult(
        ok=True,
        mode="shadow",
        report_path=report_path,
        trajectory_path=traj_path,
        draft_path=None,
        error=None,
        report=report,
    )


def run_guarded(
    *,
    issue_path: Path | str,
    artifact_dir: Path | str,
    approval_raw: Mapping[str, Any],
    headers: Mapping[str, str] | None = None,
    body: Mapping[str, object] | None = None,
) -> RunResult:
    reject_body_actor(body)
    actor = actor_from_trust_headers(headers)
    issue = load_issue(issue_path)
    plan = build_plan(issue)
    run_id = f"guarded-{uuid4().hex[:10]}"
    out = Path(artifact_dir) / run_id

    try:
        approval = parse_approval(approval_raw)
        assert_plan_bound(approval, plan.plan_sha256)
        if not approval.allow_external_write:
            raise ApprovalError(
                "allow_external_write must be true to open Draft PR "
                "(approval alone is not enough)"
            )
    except ApprovalError as exc:
        return _failed_guarded(
            out=out,
            run_id=run_id,
            actor=actor,
            plan=plan,
            issue_path=issue_path,
            error=str(exc),
        )

    draft = {
        "draft": True,
        "title": f"[draft] {plan.title}",
        "body": (
            f"Controlled delivery for {plan.issue_id}.\n"
            f"plan_sha256: {plan.plan_sha256}\n"
            f"approver: {approval.approver}\n"
            f"actor: {actor.actor_id}\n"
        ),
        "base_ref": plan.base_ref,
        "head_ref": f"agent/{plan.issue_id.lower()}",
        "repository": plan.repository,
        "plan_sha256": plan.plan_sha256,
        "mock": True,
        "created_at": _utc_now(),
    }
    draft_path = out / "draft_pr.json"
    _write_json(draft_path, draft)

    traj = build_format_b_trajectory(
        query=f"Open Draft PR for issue {plan.issue_id}",
        final_answer=f"draft opened (mock); plan_sha256={plan.plan_sha256}",
        steps=_shadow_steps(plan)
        + [
            {
                "step": 3,
                "thought": "Verify approval pins plan_sha256 then open Draft PR",
                "tool_calls": [
                    {
                        "name": "create_draft_pr",
                        "arguments": {
                            "plan_sha256": plan.plan_sha256,
                            "allow_external_write": True,
                            "mock": True,
                        },
                    }
                ],
                "observation": f"draft_pr={draft_path.name}",
            }
        ],
        task_episode_id=plan.issue_id,
        acceptance_criteria=list(plan.acceptance_criteria),
        session_id=run_id,
    )
    report = {
        "schema": "change-delivery-report/v1",
        "mode": "guarded",
        "run_id": run_id,
        "ok": True,
        "actor": {"actor_id": actor.actor_id, "source": actor.source},
        "plan": plan.to_dict(),
        "plan_sha256": plan.plan_sha256,
        "issue_path": str(issue_path),
        "approval": approval.to_dict(),
        "external_writes": ["mock_draft_pr"],
        "draft_pr": str(draft_path),
        "created_at": _utc_now(),
        "format_b": {"compatible": True, "missing_fields": []},
    }
    report_path = out / "report.json"
    traj_path = out / "trajectory.format-b.json"
    _write_json(report_path, report)
    _write_json(traj_path, traj)
    return RunResult(
        ok=True,
        mode="guarded",
        report_path=report_path,
        trajectory_path=traj_path,
        draft_path=draft_path,
        error=None,
        report=report,
    )


def _failed_guarded(
    *,
    out: Path,
    run_id: str,
    actor: CaseActor,
    plan: DeliveryPlan,
    issue_path: Path | str,
    error: str,
) -> RunResult:
    report = {
        "schema": "change-delivery-report/v1",
        "mode": "guarded",
        "run_id": run_id,
        "ok": False,
        "actor": {"actor_id": actor.actor_id, "source": actor.source},
        "plan": plan.to_dict(),
        "plan_sha256": plan.plan_sha256,
        "issue_path": str(issue_path),
        "external_writes": [],
        "draft_pr": None,
        "error": error,
        "created_at": _utc_now(),
    }
    report_path = out / "report.json"
    traj = build_format_b_trajectory(
        query=f"Guarded delivery blocked for {plan.issue_id}",
        final_answer=f"blocked: {error}",
        steps=[
            {
                "step": 1,
                "thought": "Refuse Draft PR",
                "tool_calls": [{"name": "deny_draft_pr", "arguments": {"reason": error}}],
                "observation": error,
            }
        ],
        task_episode_id=plan.issue_id,
        acceptance_criteria=list(plan.acceptance_criteria),
        session_id=run_id,
    )
    traj_path = out / "trajectory.format-b.json"
    _write_json(report_path, report)
    _write_json(traj_path, traj)
    return RunResult(
        ok=False,
        mode="guarded",
        report_path=report_path,
        trajectory_path=traj_path,
        draft_path=None,
        error=error,
        report=report,
    )


# Re-export for callers that catch trust-header failures at the boundary.
__all__ = [
    "RunResult",
    "run_shadow",
    "run_guarded",
    "ActorAuthorizationError",
]
