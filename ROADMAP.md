# Roadmap

Forward-looking only. Already shipped: pluggable per-adapter actions
(`extra_actions` in `lib-arcade`), the list + detail-pane UI (replacing the
card grid), start/stop pinned at the top of the detail pane with
server-specific actions in their own labeled section below, and greying
those out while a server is offline.

Explicit, permanent decision: **no generic "edit any server variable" UI**.
Curated presets and named toggles are the intended ceiling, not a stepping
stone toward full config editing. Auth also stays out of scope — same
no-auth/LAN-VPN-trust posture as today, revisit only if it becomes an
actual problem.

## Live stats in the detail view

Each adapter should report its current effective status (map, gamemode,
current player count/roster, etc.) via a new field on `GET /arcade/info`
(or a new endpoint). The portal proxies/aggregates this into
`/api/servers`; the existing detail pane renders it. Still read-only — no
write path, git + CI stays authoritative for anything not covered by a
preset/toggle below.

## Parameterized actions: presets and toggles

`POST /api/servers/<id>/actions/<action>` currently forwards a hardcoded
empty body (`b"{}"`) from the portal to the adapter — this needs to become
"forward whatever the browser actually POSTs" so an action can carry
arguments. The detail pane needs a small form/select per parameterized
action, not just a button. First real feature (adapter-side work lives in
`arcade-cs2`): a casual/competitive economy preset applied via RCON, the
same live-`changelevel`-style path already proven for map switching.

## Broaden to other adapters

Once presets/toggles exist for one game, extend the same pattern (curated,
not raw config) to Minecraft and Palworld using whatever each one's own
control surface supports — genuinely game-by-game, inside each adapter.
