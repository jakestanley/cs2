"""In-memory registry for dynamically self-registered arcade adapters.

Separate from the static `variants:` config used by cs2/sandstorm — see
docs/ARCADE_CONTRACT.md. Thread-safe; the portal's ThreadingHTTPServer
handles requests concurrently.
"""

from __future__ import annotations

import threading
import time

STALE_AFTER_SECONDS = 90.0

_lock = threading.Lock()
_registrations: dict[str, dict] = {}


def register(payload: dict) -> None:
    server_id = str(payload.get("id") or "").strip()
    if not server_id:
        raise ValueError("registration missing 'id'")
    base_url = str(payload.get("base_url") or "").strip()
    if not base_url:
        raise ValueError("registration missing 'base_url'")
    actions = payload.get("actions")
    if not isinstance(actions, list):
        actions = []
    stats = payload.get("stats")
    if not isinstance(stats, list):
        stats = []
    entry = {
        "id": server_id,
        "name": str(payload.get("name") or server_id),
        "description": str(payload.get("description") or ""),
        "base_url": base_url.rstrip("/"),
        "actions": [a for a in (_normalize_action(a) for a in actions) if a is not None],
        "stats": stats,
        "status": str(payload.get("status") or "unknown"),
        # Optional -- an adapter that's never heard of update checking
        # (or one on an old lib-arcade version) just omits it, and the
        # portal treats that exactly like "no update", never like an error.
        "update_available": bool(payload.get("update_available")),
        "last_seen": time.time(),
    }
    with _lock:
        _registrations[server_id] = entry


def _normalize_action(action) -> str | dict:
    """An action is either a bare name (str) or a parameterized action
    (dict with at least a string 'name') -- see docs/ARCADE_CONTRACT.md.
    Anything else is dropped rather than passed through malformed, since
    the portal never interprets an action beyond its name."""
    if isinstance(action, dict):
        name = action.get("name")
        return action if isinstance(name, str) and name else None
    return str(action)


def action_names(entry: dict) -> set[str]:
    """Names only, regardless of whether an entry is a bare string or a
    parameterized-action dict -- used for the portal's action-validity
    check, which never needs to look at 'params'."""
    return {
        a if isinstance(a, str) else a.get("name")
        for a in entry.get("actions", [])
    }


def list_active() -> list[dict]:
    cutoff = time.time() - STALE_AFTER_SECONDS
    with _lock:
        active = [dict(v) for v in _registrations.values() if v["last_seen"] >= cutoff]
    for entry in active:
        entry.pop("last_seen", None)
    active.sort(key=lambda e: e["name"].lower())
    return active


def update_status(server_id: str, status: str) -> None:
    """Opportunistic refresh after a successful action call — avoids the
    up-to-90s staleness of waiting for the next heartbeat. A successful
    action call is itself proof of liveness, same as a heartbeat, so this
    also bumps last_seen."""
    with _lock:
        entry = _registrations.get(server_id)
        if entry is not None:
            entry["status"] = status
            entry["last_seen"] = time.time()


def get(server_id: str) -> dict | None:
    cutoff = time.time() - STALE_AFTER_SECONDS
    with _lock:
        entry = _registrations.get(server_id)
        if entry is None or entry["last_seen"] < cutoff:
            return None
        return dict(entry)
