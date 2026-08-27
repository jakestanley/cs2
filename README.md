# Arcade

`arcade.stanley.arpa` — a uniform, cross-host control interface for game servers (and eventually
other services). Pure presentation and API aggregation: it does not manage Docker, systemd, or
any game process directly, and needs no elevated host access anywhere.

Server management lives entirely in each managed server's own **adapter** — a small HTTP service,
in its own standalone `arcade-<game>` repo (e.g. `arcade-palworld`, controlling `docker-palworld`),
that exposes `GET /arcade/info` and `POST /arcade/actions/<action>` and heartbeat-registers itself
with this portal. See `docs/ARCADE_CONTRACT.md` for the full contract.

Ingress and ports are defined by `homelab-infra/registry.yaml` (service name: `arcade`).

## Run

```bash
cp .env.example .env
# set BOT_TOKEN (from @BotFather) and ALLOWED_USER_IDS, or the telegram-bot
# service will refuse to start / reject every side-effecting command
./scripts/up.sh
```

`scripts/up.sh` is idempotent: it resolves `PORTAL_PORT` from `../homelab-infra/registry.yaml`
(override via `.env` if needed) and runs `docker compose up -d --build`. That's the entire
deployment — no systemd units, no venvs, no sudo.

Open `http://<host>:<portal_port>` for the portal.

## Telegram bot

`telegram-bot/` — a Telegram front-end for the same API the web UI uses, as its own sibling
Compose service (not a separate repo — see `homelab-standards/PATTERNS/telegram-bot.md`).
Commands are derived from `/api/servers` at call time, so a new registered game server needs no
new bot code:

- `/status` — list registered servers and their status (open to anyone).
- `/start_server` / `/stop_server` — with no argument, shows a button per server currently
  eligible for that action (only stopped servers to start, only running ones to stop); an id can
  still be passed directly (`/start_server arcade-palworld`) to skip the menu. Restricted to
  `ALLOWED_USER_IDS` (comma-separated Telegram user IDs; find yours via @userinfobot), re-checked
  on every button press too, not just when the command is run. Fails closed — empty/unset means
  nobody can run these, not everybody.

(`/start` itself is reserved by Telegram for the client's own onboarding message, hence
`start_server`/`stop_server` rather than plain `start`/`stop`.)

## API

- `GET /api/servers` — currently-registered servers (id, name, description, actions, status).
- `POST /api/register` — adapters call this to register/heartbeat (see `docs/ARCADE_CONTRACT.md`).
- `POST /api/servers/<id>/actions/<action>` — proxies to the registered server's adapter.

## Notes

- No authentication — trusts the homelab LAN/VPN, per `homelab-standards/PATTERNS/api.md`'s
  default posture. Do not expose the portal port outside the LAN.
- Registrations are in-memory only (`registry.py`), by design: a server whose adapter stops
  heartbeating (e.g. the whole host goes offline) disappears from `/api/servers` after 90s, and
  reappears automatically the moment its adapter starts heartbeating again — no manual cleanup,
  no stale zombie entries, no persistence to carry across a portal restart. This is intentional,
  not a gap.
- Legacy `cs2`/`sandstorm` direct-process-management variants (and the static `variants:`
  config mechanism they used) have been removed — that pattern conflated portal presentation
  with per-game server management, which is exactly what the adapter model above replaces.
