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
    entry = {
        "id": server_id,
        "name": str(payload.get("name") or server_id),
        "description": str(payload.get("description") or ""),
        "base_url": base_url.rstrip("/"),
        "actions": [str(a) for a in actions],
        "status": str(payload.get("status") or "unknown"),
        "last_seen": time.time(),
    }
    with _lock:
        _registrations[server_id] = entry


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
