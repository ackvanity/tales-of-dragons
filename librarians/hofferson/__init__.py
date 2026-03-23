"""
librarians/hofferson/__init__.py — Hofferson data helpers.

Provides get_humans(), which loads the list of all tracked NPC character
IDs from data/character/human/humans.json.
"""

from librarians import core


def get_humans() -> list[str]:
    """
    Return the list of all NPC character IDs tracked by the engine.

    Reads data/character/human/humans.json, which is a plain JSON array
    of id strings (e.g. ["hiccup", "astrid"]).

    Raises:
        ValueError: If the file does not contain a JSON list.
        FileNotFoundError: If humans.json does not exist.
    """
    data = core.get_data("character/human/humans")
    if not isinstance(data, list):
        raise ValueError(f"Expected list from humans data, got {type(data)}")
    return data
