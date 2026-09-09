![Abraxas Labs](docs/banner.png)

# Mintranet

Invite-only island intranet. Friends join one Owner house over WireGuard. House services have no standing path to the public Internet.

**This project is in active development and is not stable.** Interfaces, on-disk formats, and Compose service names may change without a migration path. Do not treat a running island as production data you cannot rebuild.

Copyright Abraxas. License: AGPLv3.

## Features

- One Owner island, IPv4 only, prefix `10.77.0.0/24`
- WireGuard star hub on UDP/51820; certificates only; no pre-shared key; no member mesh
- Names under `.min` with Owner-published DNS
- Island CA (ECDSA P-384) and HTTPS on the house wire after first boot
- Invite join by one-time link, QR, or short code
- One Member bound to one device (laptop or Raspberry Pi in v1)
- Limited join until the house template is accepted
- Static cottage page per Member (`www.name.min`)
- IRC on Ergo (`#house`, `#help`); nickname is the Member name; no chat archive
- Owner-only temporary egress (15 minutes, auto-off, audited)
- Owner masquerade for support (30 minutes, reason required, audited, Member notified)
- Recovery kit download; no cryptographic backdoor
- Phone-simple GUI that is only an API client
- Operator CLI and a device agent that does not display PEM files

## Status

v0.1 control plane and Compose layout. Laboratory tags, not digest-pinned production images. Client-certificate enforcement is the intended mode; `MINTRANET_ALLOW_DEV_AUTH` is a lab bypass and must stay off on a house that has guests.

Phones, mesh WireGuard, email, SFTP, Kubernetes, federation, and a second CA are out of scope.

## Containers

One Compose file. One container per service. Default profile is the Owner core. Optional work is behind Compose profiles.

| Service | Image | Role |
|---|---|---|
| `api` | local `mintranet/api` | Source of truth. Versioned REST `/v1`. SQLite identity store. Island CA. Zone, WireGuard, and Caddy publication. |
| `gui` | local `mintranet/gui` | Browser UI. Renders API data only. |
| `caddy` | `caddy` | TLS terminator and virtual hosts for `house.min` and service names. |
| `coredns` | `coredns` | Authoritative DNS for `.min`. Reloads the published zone. |
| `origin` | `nginx` | Serves each Member static site from the data volume. |
| `ergo` | `ergochat/ergo` | Island IRC. Default rooms `#house` and `#help`. |
| `unbound` | profile `recursor` | Recursive resolver on the Owner. Member Pi recursors remain opt-in. |
| `forgejo` | profile `git` | One git service. An organization per Member plus the Owner. |
| `step-ca` | profile `ca-acme` | Optional ACME front. First boot already mints the island root in the API. |
| `dnsmasq` | profile `dhcp` | IPv4 allocator on the overlay. Host network; not required for a lab API run. |

Host-side, not containers:

- Owner host agent applies published `wg0.conf` and default-deny nftables
- Member agent creates device keys, joins, installs the island CA, and brings up `wg0`
- chrony is expected on the Owner host for island time

## Coordinates

| Item | v1 value |
|---|---|
| TLD | `.min` |
| Prefix | `10.77.0.0/24` |
| Owner | `10.77.0.1` |
| DHCP | `10.77.0.50`-`10.77.0.200` |
| Overlay | WireGuard star, UDP/51820 |
| House names | `house.min`, `api.house.min`, `ca.house.min`, `ns.house.min`, `irc.house.min`, `git.house.min` |
| Session | client certificate, then 12-hour JWT for browsers |
| Floor | 4 GB RAM, Raspberry Pi OS / Debian / Ubuntu |

## Laboratory control plane

Docker is not required to exercise the API.

```bash
python3 -m venv .venv
.venv/bin/pip install -r api/requirements.txt
make test
MINTRANET_DATA_DIR="$PWD/data" MINTRANET_ALLOW_DEV_AUTH=true \
  PYTHONPATH=api .venv/bin/uvicorn app.main:app --app-dir api --host 127.0.0.1 --port 8081
```

First boot:

```bash
python3 cli/mintranet.py --api http://127.0.0.1:8081 bootstrap \
  --display-name "The Stilts" --owner-name keeper
```

Serve `gui/public` with any static server, or start Compose and open the GUI on the loopback HTTP port.

## Owner host

Raspberry Pi OS, Debian, or Ubuntu. 4 GB RAM or more.

```bash
sudo ./install.sh
sudo docker compose build api gui
sudo docker compose up -d
```

Complete first boot in the GUI and store the recovery kit immediately. If the kit and the disk passphrase are both lost, the island cannot be restored.

Optional profiles:

```bash
sudo docker compose --profile git --profile recursor up -d
```

Compose file tags are laboratory version pins. A production apply requires digest pins and a signature check after the Owner opens the egress gate. Use `scripts/pin-images.sh`, record digests, verify, then apply.

## Member device

```bash
python3 agent/mintranet-agent.py --api https://house.min --code ABCDEF --name sam --device-class laptop
```

The agent generates the device key, submits the join, writes `wg0`, and installs the island CA. After join the Member is limited (resolve, published sites, IRC) until the house setup is accepted.

## API surface

Unauthenticated: `GET /v1/health`, `GET /v1/island`, `GET /v1/join/{code}`, `POST /v1/island/bootstrap`, `POST /v1/join`.

Authenticated: users, invites, DNS names and requests, templates, masquerade, egress, sites, audit, recovery kit.

## Threat model

v1 is built first against a malicious guest on the LAN. House paths default-deny egress. The Member host NIC may still use the public Internet. Treat `MINTRANET_ALLOW_DEV_AUTH` as an unlocked door.
