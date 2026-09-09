#!/usr/bin/env python3
"""Operator CLI. Same API as the GUI."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request


def call(base: str, path: str, token: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Authorization": token},
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def auth_header(args: argparse.Namespace) -> str:
    if args.dev_as:
        return f"Dev {args.dev_as}"
    if args.token:
        return f"Bearer {args.token}"
    raise SystemExit("Pass --token or --dev-as.")


def main() -> int:
    parser = argparse.ArgumentParser(prog="mintranet")
    parser.add_argument("--api", default=os.environ.get("MINTRANET_API", "http://127.0.0.1:8081"))
    parser.add_argument("--token", default=os.environ.get("MINTRANET_TOKEN", ""))
    parser.add_argument("--dev-as", default=os.environ.get("MINTRANET_DEV_AS", ""))
    sub = parser.add_subparsers(dest="cmd", required=True)

    boot = sub.add_parser("bootstrap")
    boot.add_argument("--display-name", required=True)
    boot.add_argument("--owner-name", required=True)
    boot.add_argument("--timezone", default="America/Los_Angeles")

    sub.add_parser("status")
    sub.add_parser("people")
    invite = sub.add_parser("invite")
    invite.add_argument("--role", default="Member")
    join = sub.add_parser("join-preview")
    join.add_argument("code")
    eg = sub.add_parser("egress-open")
    eg.add_argument("--reason", required=True)
    sub.add_parser("egress-close")
    mask = sub.add_parser("masquerade")
    mask.add_argument("--as-name", required=True)
    mask.add_argument("--reason", required=True)
    sub.add_parser("masquerade-end")
    sub.add_parser("audit")

    args = parser.parse_args()
    if args.cmd == "bootstrap":
        out = call(
            args.api,
            "/v1/island/bootstrap",
            "",
            "POST",
            {
                "display_name": args.display_name,
                "owner_name": args.owner_name,
                "timezone": args.timezone,
            },
        )
        print(json.dumps(out, indent=2))
        return 0

    token = auth_header(args)
    routes = {
        "status": ("/v1/island", "GET", None),
        "people": ("/v1/users", "GET", None),
        "invite": ("/v1/invites", "POST", {"intended_role": args.role if args.cmd == "invite" else "Member"}),
        "join-preview": (f"/v1/join/{args.code}" if args.cmd == "join-preview" else "/v1/health", "GET", None),
        "egress-open": ("/v1/egress", "POST", {"reason": getattr(args, "reason", "")}),
        "egress-close": ("/v1/egress", "DELETE", None),
        "masquerade": ("/v1/masquerade", "POST", {"target_name": getattr(args, "as_name", ""), "reason": getattr(args, "reason", "")}),
        "masquerade-end": ("/v1/masquerade", "DELETE", None),
        "audit": ("/v1/audit", "GET", None),
    }
    path, method, payload = routes[args.cmd]
    print(json.dumps(call(args.api, path, token, method, payload), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
