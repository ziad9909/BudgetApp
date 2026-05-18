"""Catalog of popular subscription brands with logo metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SERVICES_PATH = Path(__file__).resolve().parent / "subscription_services.json"


@lru_cache(maxsize=1)
def load_subscription_services() -> list[dict[str, Any]]:
    with SERVICES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("subscription_services.json must be a JSON array")
    return data


@lru_cache(maxsize=1)
def get_services_lookup() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in load_subscription_services()}


def get_service_by_id(service_id: str) -> dict[str, Any] | None:
    if not service_id:
        return None
    return get_services_lookup().get(service_id.strip())


def get_service_by_name(name: str) -> dict[str, Any] | None:
    key = name.strip().lower()
    if not key:
        return None
    for service in load_subscription_services():
        if service["name"].lower() == key:
            return service
    for service in load_subscription_services():
        if key in service["name"].lower() or service["name"].lower() in key:
            return service
    return None


def resolve_subscription_brand(service_key: str = "", name: str = "") -> dict[str, Any] | None:
    brand = get_service_by_id(service_key)
    if brand:
        return brand
    return get_service_by_name(name)


def logo_url(service: dict[str, Any]) -> str | None:
    slug = (service.get("icon_slug") or "").strip()
    if not slug:
        return None
    return f"https://cdn.simpleicons.org/{slug}/white"


GROUP_LABELS: dict[str, str] = {
    "streaming": "Streaming & TV",
    "music": "Music",
    "gaming": "Gaming",
    "software": "Apps & Software",
    "fitness": "Fitness & Lifestyle",
}

GROUP_ORDER: tuple[str, ...] = ("streaming", "music", "gaming", "software", "fitness")


def get_service_groups() -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {g: [] for g in GROUP_ORDER}
    for service in load_subscription_services():
        if service.get("id") == "other":
            continue
        group = service.get("group") or "software"
        if group not in buckets:
            buckets[group] = []
        buckets[group].append(service)
    return [
        {"id": gid, "label": GROUP_LABELS.get(gid, gid.title()), "services": buckets[gid]}
        for gid in GROUP_ORDER
        if buckets.get(gid)
    ]
