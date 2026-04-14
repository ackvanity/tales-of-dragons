"""
librarians/core.py — Data file loader.

Central utility for loading game data files from the data/ directory.
All game content (characters, locations, quest scripts) is loaded through
get_data(), which handles both JSON and raw text files.
"""

import json
from typing import Iterable
import haddock
import os

SAVE_DIRECTORY = "saves"
"""Directory where save files will be written (not yet implemented)."""

DATA_DIRECTORY = "data"
"""Root directory for all game content files."""

TCSS_DIRECTORY = "tcss"


def get_data(
    path: Iterable[str] | str,
    ext: str = "json",
    parse: bool = True,
) -> object:
    """
    Load a data file from the data/ directory.

    Args:
        path:  File path relative to data/, without extension. Can be a
               string ("character/human/hiccup") or a list of path segments
               (["quest", "rescue_hiccup_toothless"]).
        ext:   File extension (default "json"). Use "py" for quest scripts.
        parse: If True (default), parse JSON and return a Python object.
               If False, return the raw file contents as a string.

    Returns:
        Parsed JSON object (dict or list) when parse=True,
        or raw string content when parse=False.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not isinstance(path, str):
        path = "/".join(path)

    try:
        with open(f"{DATA_DIRECTORY}/{path}.{ext}", "r") as f:
            if parse:
                return json.load(f)
            return f.read()
    except FileNotFoundError:
        raise


def parse_save_file(file: str) -> tuple[str, str] | None:
    try:
        hiccup = haddock.Hiccup()
        hiccup.load(f"{SAVE_DIRECTORY}/{file}")
        name = hiccup.call_entity(haddock.EntityID("jorgenson", "player", "player")).name  # type: ignore
        return (file, name)
    except Exception as e:
        print(f"Cannot parse file f{file}. Exception: {e}")
        return None


def get_save_files() -> list[tuple[str, str]]:
    print("loaddragonsavefiles")
    files: list[tuple[str, str]] = []
    for save in os.listdir(f"{SAVE_DIRECTORY}"):
        print("parsefilefromsave")
        print(save)
        parsed = parse_save_file(save)
        if parsed:
            files.append(parsed)
    return files
