"""Hostname rules locked for v1."""

from __future__ import annotations

import re

from .config import settings

LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,22}[a-z0-9])?$")


class NameError(ValueError):
    pass


def validate_member_name(name: str) -> str:
    candidate = name.strip().lower()
    if not 2 <= len(candidate) <= 24:
        raise NameError("Name must be 2 to 24 characters.")
    if not LABEL_RE.fullmatch(candidate):
        raise NameError("Use lowercase letters, digits, and hyphens only.")
    if candidate in settings.reserved:
        raise NameError(f"'{candidate}' is reserved by the house.")
    return candidate


def member_fqdn(name: str) -> str:
    return f"{name}.{settings.tld}"


def house_fqdn(label: str) -> str:
    return f"{label}.house.{settings.tld}"
