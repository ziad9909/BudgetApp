"""Load and validate the default financial category catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

CategoryType = Literal["expense", "income"]

CATEGORIES_PATH = Path(__file__).resolve().parent / "categories.json"
REQUIRED_FIELDS = frozenset({"id", "name", "icon", "color", "type"})
VALID_TYPES = frozenset({"expense", "income"})
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_categories() -> list[dict[str, Any]]:
    """Return all categories from the JSON catalog."""
    with CATEGORIES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("categories.json must be a JSON array")
    return data


def validate_categories(categories: list[dict[str, Any]]) -> None:
    """Raise ValueError if the catalog is invalid."""
    seen_ids: set[str] = set()

    for index, item in enumerate(categories):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {index} must be an object")

        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"Item at index {index} missing fields: {sorted(missing)}")

        cat_id = item["id"]
        if not isinstance(cat_id, str) or not cat_id.strip():
            raise ValueError(f"Item at index {index}: id must be a non-empty string")
        if cat_id in seen_ids:
            raise ValueError(f"Duplicate category id: {cat_id}")
        seen_ids.add(cat_id)

        if item["type"] not in VALID_TYPES:
            raise ValueError(f"Item '{cat_id}': type must be 'expense' or 'income'")

        if not HEX_COLOR_PATTERN.match(item["color"]):
            raise ValueError(f"Item '{cat_id}': color must be a 6-digit hex (e.g. #FF6B6B)")

        expected_prefix = "exp_" if item["type"] == "expense" else "inc_"
        if not cat_id.startswith(expected_prefix):
            raise ValueError(
                f"Item '{cat_id}': id should start with '{expected_prefix}' for type '{item['type']}'"
            )


def get_categories_by_type(category_type: CategoryType) -> list[dict[str, Any]]:
    """Filter categories by expense or income."""
    return [c for c in load_categories() if c["type"] == category_type]


def get_category_by_id(category_id: str) -> dict[str, Any] | None:
    """Look up a single category by stable id."""
    for category in load_categories():
        if category["id"] == category_id:
            return category
    return None


def get_category_names(category_type: CategoryType | None = None) -> list[str]:
    """Return display names, optionally filtered by type."""
    categories = load_categories()
    if category_type:
        categories = [c for c in categories if c["type"] == category_type]
    return [c["name"] for c in categories]


def get_category_by_name(name: str) -> dict[str, Any] | None:
    """Look up a category by its display name."""
    key = name.strip()
    if not key:
        return None
    for category in load_categories():
        if category["name"] == key:
            return category
    return None


def get_category_lookup() -> dict[str, dict[str, Any]]:
    """Map display name -> category record (for templates and reports)."""
    return {c["name"]: c for c in load_categories()}


def validate_category_for_type(name: str, category_type: CategoryType) -> tuple[bool, str]:
    """
  Validate that `name` is a catalog category matching `category_type`.
  Returns (ok, resolved_name_or_error_message).
    """
    category = get_category_by_name(name)
    if not category:
        return False, "Please select a valid category."
    if category["type"] != category_type:
        return False, "Category does not match the transaction type."
    return True, category["name"]


def export_for_api() -> dict[str, list[dict[str, Any]]]:
    """Shape suitable for REST/mobile clients: grouped by type."""
    categories = load_categories()
    return {
        "expense_categories": [c for c in categories if c["type"] == "expense"],
        "income_categories": [c for c in categories if c["type"] == "income"],
    }


if __name__ == "__main__":
    catalog = load_categories()
    validate_categories(catalog)
    grouped = export_for_api()

    print("Financial Category Catalog — validation OK\n")
    print(f"  Total categories : {len(catalog)}")
    print(f"  Expense categories: {len(grouped['expense_categories'])}")
    print(f"  Income categories : {len(grouped['income_categories'])}")
    print(f"  Source file       : {CATEGORIES_PATH}\n")

    print("Expense Categories:")
    for cat in grouped["expense_categories"]:
        print(f"  [{cat['id']}] {cat['name']}  {cat['icon']}  {cat['color']}")

    print("\nIncome Categories:")
    for cat in grouped["income_categories"]:
        print(f"  [{cat['id']}] {cat['name']}  {cat['icon']}  {cat['color']}")
