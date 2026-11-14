"""P1-A … P1-H acceptance tests for the minimal demo slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from change_delivery.actor import ActorAuthorizationError, actor_from_trust_headers, reject_body_actor
from change_delivery.pipeline import run_guarded, run_shadow
from change_delivery.plan import build_plan, load_issue
from change_delivery.trajectory import validate_format_b_shape

ROOT = Path(__file__).resolve().parents[1]
ISSUE = ROOT / "fixtures" / "issue.json"
TRUST = {"X-Actor-Id": "approver-demo"}


def test_p1_a_shadow_emits_stable_plan_sha256(tmp_path: Path) -> None:
    issue = load_issue(ISSUE)
    plan = build_plan(issue)
    result = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    assert result.ok
    assert result.report["mode"] == "shadow"
    assert result.report["plan_sha256"] == plan.plan_sha256
    assert result.report["plan"]["issue_id"] == "P1-DEMO-001"
    again = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    assert again.report["plan_sha256"] == plan.plan_sha256


def test_p1_b_shadow_has_no_external_writes(tmp_path: Path) -> None:
    result = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    assert result.report["mode"] == "shadow"
    assert result.report["external_writes"] == []
    assert result.report["draft_pr"] is None
    assert result.draft_path is None


def test_p1_c_matching_approval_required(tmp_path: Path) -> None:
    shadow = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    digest = shadow.report["plan_sha256"]
    missing = run_guarded(
        issue_path=ISSUE,
        artifact_dir=tmp_path,
        approval_raw={
            "approver": "reviewer@example.com",
            "approved_at": "2026-11-14T12:00:00+08:00",
            "allow_external_write": True,
        },
        headers=TRUST,
    )
    assert not missing.ok
    assert missing.draft_path is None

    ok = run_guarded(
        issue_path=ISSUE,
        artifact_dir=tmp_path,
        approval_raw={
            "plan_sha256": digest,
            "approver": "reviewer@example.com",
            "approved_at": "2026-11-14T12:00:00+08:00",
            "allow_external_write": True,
        },
        headers=TRUST,
    )
    assert ok.ok
    assert ok.draft_path is not None


def test_p1_d_stale_fingerprint_blocks_draft(tmp_path: Path) -> None:
    result = run_guarded(
        issue_path=ISSUE,
        artifact_dir=tmp_path,
        approval_raw={
            "plan_sha256": "0" * 64,
            "approver": "reviewer@example.com",
            "approved_at": "2026-11-14T12:00:00+08:00",
            "allow_external_write": True,
        },
        headers=TRUST,
    )
    assert not result.ok
    assert result.draft_path is None
    assert result.report["external_writes"] == []
    assert "plan_sha256" in (result.error or "")


def test_p1_e_allow_external_write_gate(tmp_path: Path) -> None:
    shadow = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    digest = shadow.report["plan_sha256"]
    denied = run_guarded(
        issue_path=ISSUE,
        artifact_dir=tmp_path,
        approval_raw={
            "plan_sha256": digest,
            "approver": "reviewer@example.com",
            "approved_at": "2026-11-14T12:00:00+08:00",
            "allow_external_write": False,
        },
        headers=TRUST,
    )
    assert not denied.ok
    assert denied.draft_path is None

    allowed = run_guarded(
        issue_path=ISSUE,
        artifact_dir=tmp_path,
        approval_raw={
            "plan_sha256": digest,
            "approver": "reviewer@example.com",
            "approved_at": "2026-11-14T12:00:00+08:00",
            "allow_external_write": True,
        },
        headers=TRUST,
    )
    assert allowed.ok
    draft = json.loads(allowed.draft_path.read_text(encoding="utf-8"))
    assert draft["draft"] is True
    assert draft["mock"] is True
    assert draft["plan_sha256"] == digest


def test_p1_f_body_actor_rejected() -> None:
    with pytest.raises(ActorAuthorizationError):
        reject_body_actor({"actor_id": "evil"})
    with pytest.raises(ActorAuthorizationError):
        actor_from_trust_headers({})
    actor = actor_from_trust_headers({"X-Actor-Id": "alice"})
    assert actor.actor_id == "alice"
    assert actor.source == "trust_header"

    with pytest.raises(ActorAuthorizationError):
        run_shadow(
            issue_path=ISSUE,
            artifact_dir=Path("."),
            headers=TRUST,
            body={"user_id": "spoofed"},
        )


def test_p1_g_format_b_trajectory(tmp_path: Path) -> None:
    result = run_shadow(issue_path=ISSUE, artifact_dir=tmp_path, headers=TRUST)
    traj = json.loads(result.trajectory_path.read_text(encoding="utf-8"))
    assert validate_format_b_shape(traj) == []
    assert traj["schema_version"] == "1"
    assert "format-b" in traj["format"]
    assert len(traj["steps"]) >= 1


def test_p1_h_no_react_loop_or_go_tree() -> None:
    banned_names = {"react_loop.py", "react_loop", "go.mod", "main.go"}
    found: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or "artifacts" in path.parts:
            continue
        if path.name in banned_names:
            found.append(str(path.relative_to(ROOT)))
        if path.suffix == ".go":
            found.append(str(path.relative_to(ROOT)))
    assert found == [], f"P1-H violated: {found}"
