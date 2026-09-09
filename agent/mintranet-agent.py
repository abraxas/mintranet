#!/usr/bin/env python3
"""Member device agent. Creates keys locally, joins, installs trust and wg0."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import urllib.request
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Python 3 is required.") from exc


def request(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def gen_wg() -> tuple[str, str]:
    if shutil.which("wg"):
        private = subprocess.check_output(["wg", "genkey"], text=True).strip()
        public = subprocess.check_output(["wg", "pubkey"], input=private, text=True).strip()
        return private, public
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    import base64

    key = X25519PrivateKey.generate()
    private = base64.b64encode(
        key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    ).decode()
    public = base64.b64encode(
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
    return private, public


def write(path: Path, body: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(mode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Join a Mintranet house.")
    parser.add_argument("--api", default="http://10.77.0.1")
    parser.add_argument("--code", required=True, help="Invite link token or short code")
    parser.add_argument("--name", required=True)
    parser.add_argument("--device-class", choices=("laptop", "pi"), default="laptop")
    parser.add_argument("--device-name", default="")
    parser.add_argument("--state-dir", default=str(Path.home() / ".mintranet"))
    args = parser.parse_args()

    preview = request(f"{args.api}/v1/join/{args.code}")
    print(preview.get("copy", "Join the house network."))
    priv, pub = gen_wg()
    body = {
        "code": args.code,
        "name": args.name,
        "device_class": args.device_class,
        "device_name": args.device_name or args.name,
        "wg_public_key": pub,
    }
    result = request(f"{args.api}/v1/join", body)
    state = Path(args.state_dir)
    write(state / "trust" / "island-ca.crt", result["trust_bundle_pem"], 0o644)
    if result.get("certificate_pem"):
        write(state / "client.crt", result["certificate_pem"], 0o644)
    write(state / "wg.private", priv)
    wg = "\n".join(
        [
            "[Interface]",
            f"PrivateKey = {priv}",
            f"Address = {result['ipv4']}/32",
            "",
            "[Peer]",
            f"PublicKey = {result['owner_wg_public_key']}",
            f"Endpoint = {result['owner_ipv4']}:{result['wg_port']}",
            "AllowedIPs = 10.77.0.0/24",
            "PersistentKeepalive = 25",
            "",
        ]
    )
    write(state / "wg0.conf", wg)
    dest = Path("/etc/wireguard/wg0.conf")
    if os.geteuid() == 0:
        write(dest, wg)
        subprocess.run(["wg-quick", "up", "wg0"], check=False)
        ca_src = state / "trust" / "island-ca.crt"
        shutil.copy(ca_src, "/usr/local/share/ca-certificates/mintranet-island.crt")
        subprocess.run(["update-ca-certificates"], check=False)
    else:
        print(f"Wrote {state / 'wg0.conf'}. Run as root to install WireGuard and the house CA.")
    print(f"Joined as {result['fqdn']} ({result['ipv4']}).")
    print(result["impact"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
