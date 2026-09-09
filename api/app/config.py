"""Runtime configuration. Paths live on the Owner data volume."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINTRANET_", extra="ignore")

    data_dir: Path = Path("/data")
    allow_dev_auth: bool = False
    listen_host: str = "0.0.0.0"
    listen_port: int = 8081
    jwt_hours: int = 12
    invite_link_hours: int = 48
    invite_code_hours: int = 4
    invite_unused_cap: int = 10
    masquerade_minutes: int = 30
    egress_minutes: int = 15
    prefix: str = "10.77.0.0/24"
    owner_ipv4: str = "10.77.0.1"
    dhcp_start: str = "10.77.0.50"
    dhcp_end: str = "10.77.0.200"
    wg_port: int = 51820
    tld: str = "min"
    product_name: str = "Mintranet"
    reserved_labels: str = "www,api,ns,git,irc,ca,house,owner,admin,mail,ftp"

    @property
    def reserved(self) -> set[str]:
        return {item.strip() for item in self.reserved_labels.split(",") if item.strip()}

    @property
    def db_path(self) -> Path:
        return self.data_dir / "island.sqlite"

    @property
    def ca_dir(self) -> Path:
        return self.data_dir / "ca"

    @property
    def published_dir(self) -> Path:
        return self.data_dir / "published"

    @property
    def sites_dir(self) -> Path:
        return self.data_dir / "sites"

    @property
    def kit_dir(self) -> Path:
        return self.data_dir / "recovery"


settings = Settings()
