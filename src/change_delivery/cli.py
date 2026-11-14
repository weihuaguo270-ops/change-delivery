"""CLI: change-delivery shadow | guarded."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from change_delivery.actor import ActorAuthorizationError
from change_delivery.pipeline import run_guarded, run_shadow


def _headers_from_args(actor_id: str) -> dict[str, str]:
    return {"X-Actor-Id": actor_id}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="change-delivery")
    sub = parser.add_subparsers(dest="cmd", required=True)

    shadow = sub.add_parser("shadow", help="Read issue and run shadow (no Draft PR)")
    shadow.add_argument("--issue", required=True, type=Path)
    shadow.add_argument("--artifact-dir", required=True, type=Path)
    shadow.add_argument("--actor-id", required=True, help="Trusted actor id (maps to X-Actor-Id)")

    guarded = sub.add_parser("guarded", help="Open Draft PR only with matching approval")
    guarded.add_argument("--issue", required=True, type=Path)
    guarded.add_argument("--artifact-dir", required=True, type=Path)
    guarded.add_argument("--approval", required=True, type=Path)
    guarded.add_argument("--actor-id", required=True, help="Trusted actor id (maps to X-Actor-Id)")
    guarded.add_argument(
        "--body-json",
        type=Path,
        default=None,
        help="Optional request body JSON (must not contain actor fields)",
    )

    args = parser.parse_args(argv)
    headers = _headers_from_args(args.actor_id)

    try:
        if args.cmd == "shadow":
            result = run_shadow(
                issue_path=args.issue,
                artifact_dir=args.artifact_dir,
                headers=headers,
            )
        else:
            approval = json.loads(args.approval.read_text(encoding="utf-8"))
            body = None
            if args.body_json:
                body = json.loads(args.body_json.read_text(encoding="utf-8"))
            result = run_guarded(
                issue_path=args.issue,
                artifact_dir=args.artifact_dir,
                approval_raw=approval,
                headers=headers,
                body=body,
            )
    except ActorAuthorizationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    payload = {
        "ok": result.ok,
        "mode": result.mode,
        "report": str(result.report_path),
        "trajectory": str(result.trajectory_path),
        "draft_pr": str(result.draft_path) if result.draft_path else None,
        "plan_sha256": result.report.get("plan_sha256"),
        "error": result.error,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
