"""Entity model matching the locked v1 schema."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Island(Base):
    __tablename__ = "island"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(64))
    prefix: Mapped[str] = mapped_column(String(32))
    owner_ipv4: Mapped[str] = mapped_column(String(32))
    wg_public_key: Mapped[str] = mapped_column(String(64))
    wg_private_key: Mapped[str] = mapped_column(String(64))
    jwt_secret: Mapped[str] = mapped_column(String(128))
    ca_serial: Mapped[str] = mapped_column(String(64))
    zone_serial: Mapped[int] = mapped_column(Integer, default=1)
    initialized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    egress_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    egress_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(24), unique=True)
    role: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    device: Mapped["Device | None"] = relationship(back_populates="user", uselist=False)
    credentials: Mapped[list["Credential"]] = relationship(back_populates="user")
    site: Mapped["Site | None"] = relationship(back_populates="user", uselist=False)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    class_name: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(80))
    agent_state: Mapped[str] = mapped_column(String(24), default="pending")
    limited_join: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ipv4: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recursor_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="device")


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(24))
    serial: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wg_public_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped[User] = relationship(back_populates="credentials")


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    short_code: Mapped[str] = mapped_column(String(8), unique=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intended_role: Mapped[str] = mapped_column(String(16), default="Member")


class DnsName(Base):
    __tablename__ = "dns_names"
    __table_args__ = (UniqueConstraint("fqdn", name="uq_dns_fqdn"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fqdn: Mapped[str] = mapped_column(String(255))
    rtype: Mapped[str] = mapped_column(String(16))
    value: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(16), default="active")


class DnsRequest(Base):
    __tablename__ = "dns_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fqdn: Mapped[str] = mapped_column(String(255))
    rtype: Mapped[str] = mapped_column(String(16))
    value: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class TemplatePush(Base):
    __tablename__ = "template_pushes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    status: Mapped[str] = mapped_column(String(16), default="offered")
    snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Masquerade(Base):
    __tablename__ = "masquerades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(240))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    effective_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    masquerade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    fqdn: Mapped[str] = mapped_column(String(255), unique=True)
    body: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(back_populates="site")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
