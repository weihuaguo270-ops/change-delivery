"""Minimal Format B–compatible trajectory builder (field-level, no runtime migrate)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

# Compatible subset of harness_trajectory / agent_trajectory Format B.
FORMAT_B_SCHEMA = "harness_trajectory/format-b"
FORMAT_B_VERSION = "1"


def build_format_b_trajectory(
    *,
    query: str,
    final_answer: str,
    steps: list[dict[str, Any]],
    task_episode_id: str | None = None,
    acceptance_criteria: list[str] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    if not steps:
        raise ValueError("Format B trajectory requires at least one step")
    return {
        "schema_version": FORMAT_B_VERSION,
        "format": FORMAT_B_SCHEMA,
        "session_id": session_id or f"cd-{uuid4().hex[:12]}",
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_steps": len(steps),
        "final_answer": final_answer,
        "task_episode_id": task_episode_id,
        "acceptance_criteria": list(acceptance_criteria or []),
        "steps": steps,
        "model": "change-delivery-p1-demo",
    }


def validate_format_b_shape(traj: dict[str, Any]) -> list[str]:
    """Return list of missing required Format B fields (empty ⇒ shape OK)."""
    required = ("session_id", "query", "steps", "final_answer")
    missing = [k for k in required if k not in traj or traj[k] in (None, "")]
    if "steps" in traj and (not isinstance(traj["steps"], list) or len(traj["steps"]) < 1):
        missing.append("steps(non-empty)")
    return missing
