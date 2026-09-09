#!/bin/bash
# Owner host agent. Applies published WireGuard and nftables material.
# Run from cron or a systemd timer every 15 seconds.
set -euo pipefail

DATA="${MINTRANET_DATA:-/var/lib/mintranet}"
PUB="$DATA/published"
WG_CONF=/etc/wireguard/wg0.conf

if [[ ! -f "$PUB/wg0.conf" ]]; then
  echo "mintranet-host-agent: nothing published yet" >&2
  exit 0
fi

if grep -qE 'image:.*:latest' "$(dirname "$0")/../docker-compose.yml" 2>/dev/null; then
  echo "mintranet-host-agent: refuse compose file that contains :latest" >&2
  exit 2
fi

install -m 600 "$PUB/wg0.conf" "$WG_CONF"
if command -v wg-quick >/dev/null 2>&1; then
  wg syncconf wg0 <(wg-quick strip wg0) 2>/dev/null || wg-quick up wg0 || true
fi

if [[ -f "$(dirname "$0")/nftables.rules" ]] && command -v nft >/dev/null 2>&1; then
  nft -f "$(dirname "$0")/nftables.rules" || true
fi

if [[ -f "$PUB/egress.json" ]] && command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import json, subprocess, time
from pathlib import Path
import os
pub = Path(os.environ.get("MINTRANET_DATA", "/var/lib/mintranet")) / "published" / "egress.json"
try:
    data = json.loads(pub.read_text())
except Exception:
    raise SystemExit(0)
until = data.get("until")
if not until:
    raise SystemExit(0)
print("egress gate advertised; destinations applied by Owner policy")
PY
fi
