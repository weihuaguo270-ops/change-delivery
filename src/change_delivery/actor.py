"""Server-trusted actor construction. Body fields never authorize."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CaseActor:
    actor_id: str
    source: str


class ActorAuthorizationError(ValueError):
    """Raised when a caller tries to authorize via request body."""


def actor_from_trust_headers(headers: Mapping[str, str] | None) -> CaseActor:
    """Build CaseActor from trusted headers only (e.g. after Bearer auth)."""
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    actor_id = (headers.get("x-actor-id") or "").strip()
    if not actor_id:
        raise ActorAuthorizationError("missing trusted header X-Actor-Id")
    return CaseActor(actor_id=actor_id, source="trust_header")


def reject_body_actor(body: Mapping[str, object] | None) -> None:
    """Fail closed if the client tries to supply actor identity in the body."""
    if not body:
        return
    for key in ("actor_id", "actor", "user_id", "approver_id", "X-Actor-Id"):
        if key in body and body[key] not in (None, ""):
            raise ActorAuthorizationError(
                f"actor identity must not come from body field {key!r}"
            )
