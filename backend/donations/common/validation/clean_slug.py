import unicodedata


def replace_spaces_with_dashes(s: str) -> str:
    """Replace spaces with dashes in a string."""

    return s.replace(" ", "-")


def strip_accents(s: str) -> str:
    """Remove accents from a string."""

    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def remove_unwanted_characters(s: str) -> str:
    """Remove all characters from a string except for letters, numbers, and dashes."""

    return "".join(c for c in s if c.isalnum() or c == "-")


def clean_slug(slug: str) -> str:
    slug = slug.lower()
    slug = replace_spaces_with_dashes(slug)
    slug = strip_accents(slug)
    slug = remove_unwanted_characters(slug)

    return slug
