"""Helpers for normalizing user-provided transaction text."""

import re
import unicodedata


def normalize_text(value: str) -> str:
    """Collapse whitespace and trim a user-provided string."""
    return re.sub(r"\s+", " ", value).strip()


def normalize_search_key(value: str) -> str:
    """Return a lowercase, accent-insensitive key for category matching."""
    normalized = unicodedata.normalize("NFD", normalize_text(value).lower())
    return "".join(character for character in normalized if unicodedata.category(character) != "Mn")
