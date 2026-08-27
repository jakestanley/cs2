# Arcade

`arcade.stanley.arpa` — a uniform, cross-host control interface for game servers (and eventually
other services). Pure presentation and API aggregation: it does not manage Docker, systemd, or
any game process directly, and needs no elevated host access anywhere.

Server management lives entirely in each managed server's own **adapter** — a small HTTP service,
owned by that server's own repo, that exposes `GET /arcade/info` and `POST /arcade/actions/<action>`
and heartbeat-registers itself with this portal. See `docs/ARCADE_CONTRACT.md` for the full contract,
and `docker-palworld`'s `arcade/` directory for a reference adapter implementation.

Ingress and ports are defined by `homelab-infra/registry.yaml` (service name: `arcade`).

## Run

```bash
cp .env.example .env   # only needed to override PORTAL_PORT
./scripts/up.sh
```

`scripts/up.sh` is idempotent: it resolves `PORTAL_PORT` from `../homelab-infra/registry.yaml`
(override via `.env` if needed) and runs `docker compose up -d --build`. That's the entire
deployment — no systemd units, no venvs, no sudo.

Open `http://<host>:<portal_port>` for the portal.

## API

- `GET /api/servers` — currently-registered servers (id, name, description, actions, status).
- `POST /api/register` — adapters call this to register/heartbeat (see `docs/ARCADE_CONTRACT.md`).
- `POST /api/servers/<id>/actions/<action>` — proxies to the registered server's adapter.

## Notes

- No authentication — trusts the homelab LAN/VPN, per `homelab-standards/PATTERNS/api.md`'s
  default posture. Do not expose the portal port outside the LAN.
- Registrations are currently in-memory only (`registry.py`) and expire after 90s without a
  heartbeat. A server whose adapter stops heartbeating (e.g. the whole host reboots) will
  disappear from `/api/servers` until its adapter comes back — there's no persistence across a
  portal restart yet. Worth revisiting if that's a problem in practice.
- Legacy `cs2`/`sandstorm` direct-process-management variants (and the static `variants:`
  config mechanism they used) have been removed — that pattern conflated portal presentation
  with per-game server management, which is exactly what the adapter model above replaces.
