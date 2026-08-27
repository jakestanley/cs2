#!/usr/bin/env bash
# Canonical, idempotent entrypoint — starts the arcade portal via
# docker compose. Purely Docker; no host Python venv, no systemd, no sudo.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REGISTRY_SERVICE_NAME="${REGISTRY_SERVICE_NAME:-arcade}"

# Resolve PORTAL_PORT from homelab-infra's registry.yaml unless already set.
if [[ -z "${PORTAL_PORT:-}" ]]; then
  registry_path="${HOMELAB_INFRA_PATH:-$(dirname "$REPO_ROOT")/homelab-infra}/registry.yaml"
  if [[ -f "$registry_path" ]] && command -v python3 >/dev/null 2>&1; then
    resolved_port="$(python3 - "$registry_path" "$REGISTRY_SERVICE_NAME" <<'PYEOF'
import sys
try:
    import yaml
except ImportError:
    sys.exit(0)
path, service_name = sys.argv[1], sys.argv[2]
try:
    data = yaml.safe_load(open(path)) or {}
except OSError:
    sys.exit(0)
port = (data.get("services") or {}).get(service_name, {}).get("upstream", {}).get("port")
if isinstance(port, int) and port > 0:
    print(port)
PYEOF
)"
    if [[ -n "$resolved_port" ]]; then
      export PORTAL_PORT="$resolved_port"
    else
      echo "WARNING: Unable to resolve PORTAL_PORT from $registry_path; using compose default." >&2
    fi
  fi
fi

docker compose up -d --build
