#!/bin/bash
# Owner install for Raspberry Pi OS, Debian, or Ubuntu. Requires 4 GB RAM.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root." >&2
  exit 1
fi

mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
if [[ "${mem_kb}" -lt 3500000 ]]; then
  echo "Mintranet v1 expects 4 GB of RAM." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl git nftables wireguard wireguard-tools \
  docker.io docker-compose-v2 chrony openssl

install -d -m 700 /var/lib/mintranet
install -d -m 755 /usr/local/lib/mintranet
ROOT="$(cd "$(dirname "$0")" && pwd)"
cp -a "$ROOT/." /usr/local/lib/mintranet/
ln -sfn /usr/local/lib/mintranet/cli/mintranet.py /usr/local/bin/mintranet
chmod +x /usr/local/lib/mintranet/cli/mintranet.py
chmod +x /usr/local/lib/mintranet/agent/mintranet-agent.py
chmod +x /usr/local/lib/mintranet/host/mintranet-host-agent.sh

if [[ ! -f /etc/systemd/system/mintranet-host-agent.service ]]; then
  cat >/etc/systemd/system/mintranet-host-agent.service <<'UNIT'
[Unit]
Description=Mintranet owner host agent
After=network-online.target docker.service

[Service]
Type=oneshot
Environment=MINTRANET_DATA=/var/lib/mintranet
ExecStart=/usr/local/lib/mintranet/host/mintranet-host-agent.sh

[Install]
WantedBy=multi-user.target
UNIT
  cat >/etc/systemd/system/mintranet-host-agent.timer <<'UNIT'
[Unit]
Description=Refresh Mintranet host material

[Timer]
OnBootSec=20s
OnUnitActiveSec=15s
AccuracySec=5s

[Install]
WantedBy=timers.target
UNIT
  systemctl daemon-reload
  systemctl enable --now mintranet-host-agent.timer
fi

cd /usr/local/lib/mintranet
echo "Build local images, then start the core profile."
echo "  cd /usr/local/lib/mintranet && docker compose build api gui && docker compose up -d"
echo "Lab GUI: http://127.0.0.1/  API: /v1/health"
echo "Complete first boot in the GUI. Save the recovery kit immediately."
