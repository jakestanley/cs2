# Agents

## Vendored Standards

All behavioural, structural and configuration decisions must refer to vendored documentation under:
- `imported/`

## Repo Constraints (User-Provided)

- Keep a single `.env`, `.env.example`, and `requirements.txt` at repo root.
- Docker Compose only — `scripts/up.sh` running `docker compose up -d` is the sole deployment
  path. No systemd units, no NSSM, no host-level venvs.
- This repo is pure portal/presentation: it must never touch Docker, systemd, or any host
  process directly, and must never require sudo/root/elevated access anywhere. All per-server
  management lives in that server's own adapter (see `docs/ARCADE_CONTRACT.md`) — do not add
  game-specific or host-specific control logic here.
- Legacy `cs2`/`sandstorm` variants and the static `variants:` config mechanism were removed —
  do not reintroduce that pattern (portal directly managing/proxying a local game process).
