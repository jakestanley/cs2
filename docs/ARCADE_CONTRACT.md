# Arcade adapter contract (v1)

How an arbitrary game server (Docker or native, on any host) registers
itself with `arcade.stanley.arpa` and exposes actions (start/stop, and
later map changes, backups, etc.) to the portal.

This is separate from the existing static `variants:` mechanism in
`config.yaml` (used by `cs2`/`sandstorm`, which run on the same host as the
portal and are proxied at a subpath with a full embedded web UI). The
contract below is for servers that live elsewhere — possibly on a
different host, possibly Docker-based — that just need to publish a name
and a small set of actions, not a full proxied UI.

## Adapter responsibilities

A server that wants to appear in arcade implements a tiny HTTP server
("the adapter") with two endpoints, and registers itself with the portal
periodically.

### `GET /arcade/info`

Returns the adapter's current self-description. Called by the portal only
for debugging/manual checks — the portal otherwise relies on registration
heartbeats, not polling this.

```json
{
  "id": "palworld",
  "name": "Palworld",
  "description": "Palworld dedicated server (docker-palworld)",
  "actions": ["start", "stop"],
  "status": "running"
}
```

`status` is adapter-defined but should be one of `running`, `stopped`,
`unknown`.

### `POST /arcade/actions/<action>`

Triggers one of the actions the adapter declared. Must be idempotent-safe
to call when already in the target state (e.g. `start` on an
already-running server should just report the current status, not error).

Response on success (HTTP 200):

```json
{"ok": true, "status": "running"}
```

Response on failure (HTTP 4xx/5xx):

```json
{"ok": false, "error": "docker compose up failed: ..."}
```

### Registration heartbeat

The adapter calls the portal, not the other way around — this is a push
model, chosen so arcade never needs credentials/network access into other
hosts, and so a new server can be added without touching arcade's config.

```
POST http://arcade.stanley.arpa/api/register
Content-Type: application/json

{
  "id": "palworld",
  "name": "Palworld",
  "description": "Palworld dedicated server (docker-palworld)",
  "base_url": "http://adler:8300",
  "actions": ["start", "stop"],
  "status": "running"
}
```

- `id` must be stable and unique across all adapters (used as the registry
  key — re-registering the same `id` overwrites the previous entry).
- `base_url` is the adapter's own address, reachable from wherever the
  portal runs (shrike) — this is how arcade proxies action calls to a
  server on a different host without needing to know about it in advance.
- Send this on adapter startup and then repeat on an interval (recommended:
  every 30s). The portal drops a registration if it hasn't heard a
  heartbeat in 90s (3x the recommended interval) and shows the server as
  offline / removes it from the active list.
- Re-registering is how you update `status` too — there's no separate
  status-push endpoint. Include the current status on every heartbeat.

## Portal responsibilities

- `POST /api/register` — accepts the payload above, upserts it into an
  in-memory registry keyed by `id`, stamps `last_seen = now`.
- `GET /api/servers` — lists all registrations with `last_seen` within the
  90s staleness window, in the same shape as the registration payload
  (minus internal bookkeeping fields).
- `POST /api/servers/<id>/actions/<action>` — looks up the registration,
  rejects if `action` isn't in its declared `actions`, otherwise forwards
  `POST {base_url}/arcade/actions/<action>` server-side and relays the
  adapter's response back to the browser. The browser never talks to an
  adapter's `base_url` directly — only to the portal.

## Trust model (v1)

No auth between the portal and adapters, or between adapters and Docker
control on their own host. Both sides trust the homelab LAN/VPN — same
model as RCON. Do not expose adapter ports or the portal's `/api/register`
/`/api/servers/*` endpoints outside the LAN/VPN.

## Adding a new adapter for another repo

1. Implement `GET /arcade/info` and `POST /arcade/actions/<action>` for
   whatever actions make sense (start/stop at minimum).
2. Heartbeat-register with the portal on an interval.
3. Run the adapter as a small always-on process on whatever host actually
   owns that server (systemd unit, NSSM service, etc. — whatever fits that
   repo's existing runtime).

See `docker-palworld`'s `arcade/adapter.py` for a minimal reference
implementation (stdlib-only Python, wraps `docker compose`).
