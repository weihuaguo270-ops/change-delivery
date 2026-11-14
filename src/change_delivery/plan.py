"""Issue loading and plan fingerprint (plan_sha256)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeliveryPlan:
    issue_id: str
    title: str
    body: str
    repository: str
    base_ref: str
    intended_paths: tuple[str, ...]
    patch_summary: tuple[dict[str, str], ...]
    acceptance_criteria: tuple[str, ...]
    plan_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "body": self.body,
            "repository": self.repository,
            "base_ref": self.base_ref,
            "intended_paths": list(self.intended_paths),
            "patch_summary": list(self.patch_summary),
            "acceptance_criteria": list(self.acceptance_criteria),
            "plan_sha256": self.plan_sha256,
        }


def _canonical_plan_payload(raw: dict[str, Any]) -> dict[str, Any]:
    patches = raw.get("patch_summary") or []
    normalized_patches = [
        {
            "path": str(item["path"]),
            "old": str(item["old"]),
            "new": str(item["new"]),
        }
        for item in patches
    ]
    return {
        "issue_id": str(raw["issue_id"]),
        "title": str(raw["title"]),
        "body": str(raw.get("body") or ""),
        "repository": str(raw.get("repository") or ""),
        "base_ref": str(raw.get("base_ref") or "main"),
        "intended_paths": [str(p) for p in (raw.get("intended_paths") or [])],
        "patch_summary": normalized_patches,
        "acceptance_criteria": [str(c) for c in (raw.get("acceptance_criteria") or [])],
    }


def compute_plan_sha256(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def load_issue(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("issue fixture must be a JSON object")
    if "issue_id" not in data or "title" not in data:
        raise ValueError("issue fixture requires issue_id and title")
    return data


def build_plan(issue: dict[str, Any]) -> DeliveryPlan:
    payload = _canonical_plan_payload(issue)
    digest = compute_plan_sha256(payload)
    return DeliveryPlan(
        issue_id=payload["issue_id"],
        title=payload["title"],
        body=payload["body"],
        repository=payload["repository"],
        base_ref=payload["base_ref"],
        intended_paths=tuple(payload["intended_paths"]),
        patch_summary=tuple(payload["patch_summary"]),
        acceptance_criteria=tuple(payload["acceptance_criteria"]),
        plan_sha256=digest,
    )
