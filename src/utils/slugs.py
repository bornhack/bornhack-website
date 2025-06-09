from __future__ import annotations

from django.utils.text import slugify


def unique_slugify(text: str, slugs_in_use: list):
    """Use Djangos slugify and append a number if the result is in use.

    Unslugable values raise an exception. Conflict handling starts the
    numbering at 2.

    Args:
        text: The input to be slugified
        slugs_in_use: A list of strings to be checked for conflicts

    Returns:
        A string of a slug which doesn't conflict with any existing

    Raises:
        ValueError: When Djangos own slugify() returns falsy output.
    """
    slug = slugify(text)
    if not slug:
        raise ValueError("Unable to slugify input")
    if slug in slugs_in_use:
        i = 2
        slug = f"{slug}-{i}"
        while slug in slugs_in_use:
            i += 1
            slug = f"{slug[:-2]}-{i}"
    return slug
