"""Local P1 demo: shadow → approval → guarded Draft (mock) → negative mismatch."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from change_delivery.pipeline import run_guarded, run_shadow  # noqa: E402

ISSUE = ROOT / "fixtures" / "issue.json"
ART = ROOT / "artifacts" / "p1-demo"
TRUST = {"X-Actor-Id": "demo-operator"}


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    shadow = run_shadow(issue_path=ISSUE, artifact_dir=ART, headers=TRUST)
    digest = shadow.report["plan_sha256"]
    approval = {
        "plan_sha256": digest,
        "approver": "reviewer@example.com",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "allow_external_write": True,
    }
    (ART / "approval.json").write_text(
        json.dumps(approval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    guarded = run_guarded(
        issue_path=ISSUE,
        artifact_dir=ART,
        approval_raw=approval,
        headers=TRUST,
    )
    negative = run_guarded(
        issue_path=ISSUE,
        artifact_dir=ART,
        approval_raw={**approval, "plan_sha256": "f" * 64},
        headers=TRUST,
    )
    summary = {
        "shadow_ok": shadow.ok,
        "plan_sha256": digest,
        "shadow_report": str(shadow.report_path),
        "guarded_ok": guarded.ok,
        "draft_pr": str(guarded.draft_path) if guarded.draft_path else None,
        "negative_ok": negative.ok,
        "negative_draft": str(negative.draft_path) if negative.draft_path else None,
        "negative_error": negative.error,
    }
    summary_path = ART / "demo-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if shadow.ok and guarded.ok and (not negative.ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
