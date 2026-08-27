#!/usr/bin/env bash
# Canonical Linux entrypoint for homelab-arcade — generic-host systemd
# equivalent of scripts/up.ps1. See homelab-standards' systemd-service.md.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${HOMELAB_ARCADE_PYTHON_EXE:-python3}"
VENV_DIR="$REPO_ROOT/.venv"
REGISTRY_SERVICE_NAME="${REGISTRY_SERVICE_NAME:-arcade}"

preflight_check_repo() {
  local path="$1" name="$2"
  if [[ ! -d "$path" ]]; then
    echo "WARNING: $name not found at $path." >&2
    return
  fi
  if ! git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "WARNING: $name is not a git repository." >&2
    return
  fi
  if [[ -n "$(git -C "$path" status --porcelain)" ]]; then
    echo "WARNING: $name has uncommitted changes." >&2
  fi
  local branch
  branch="$(git -C "$path" rev-parse --abbrev-ref HEAD)"
  if [[ "$branch" != "main" && "$branch" != "master" ]]; then
    echo "WARNING: $name is on branch '$branch' (expected main/master)." >&2
  fi
}

if [[ "${SKIP_PREFLIGHT:-0}" != "1" ]]; then
  parent_dir="$(dirname "$REPO_ROOT")"
  infra_path="${HOMELAB_INFRA_PATH:-$parent_dir/homelab-infra}"
  standards_path="${HOMELAB_STANDARDS_PATH:-$parent_dir/homelab-standards}"
  preflight_check_repo "$infra_path" "homelab-infra"
  preflight_check_repo "$standards_path" "homelab-standards"
fi

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
VENV_PYTHON="$VENV_DIR/bin/python3"

"$VENV_PYTHON" -m pip install -q -r requirements.txt

# Resolve PORTAL_PORT from homelab-infra's registry.yaml, same lookup as up.ps1.
if [[ -z "${PORTAL_PORT:-}" ]]; then
  registry_path="${HOMELAB_INFRA_PATH:-$(dirname "$REPO_ROOT")/homelab-infra}/registry.yaml"
  if [[ -f "$registry_path" ]]; then
    resolved_port="$("$VENV_PYTHON" - "$registry_path" "$REGISTRY_SERVICE_NAME" <<'PYEOF'
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
port = (
    (data.get("services") or {}).get(service_name, {}).get("upstream", {}).get("port")
)
if isinstance(port, int) and port > 0:
    print(port)
PYEOF
)"
    if [[ -n "$resolved_port" ]]; then
      export PORTAL_PORT="$resolved_port"
    else
      echo "WARNING: Unable to resolve PORTAL_PORT from $registry_path." >&2
    fi
  fi
fi

exec "$VENV_PYTHON" "$REPO_ROOT/supervisor.py"
