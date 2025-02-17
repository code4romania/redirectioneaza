from django.utils.text import slugify


def remove_unwanted_characters(s: str) -> str:
    """Remove all characters from a string except for letters, numbers, and dashes."""

    return "".join(c for c in s if c.isalnum() or c == "-")


def clean_slug(slug: str) -> str:
    """Slugify the string but also remove underscores and other unwanted characters."""
    slug = slugify(slug)
    slug = remove_unwanted_characters(slug)

    return slug
