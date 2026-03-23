"""
librarians/hofferson/finn.py — Location data parser.

Parses raw JSON dicts (loaded from data/location/) into typed
LocationData objects consumed by clans/hofferson/finn.py.
"""

from typing import Any


class ActionData:
    """
    Raw action entry parsed from a location's JSON actions array.

    Attributes:
        line:  Button label shown to the player.
        event: Event string to be parsed by librarians/evaluator.py.
    """

    line: str
    event: str


class LocationData:
    """
    Fully parsed representation of a location JSON file.

    Attributes:
        id:          Unique identifier matching the filename.
        name:        Display name shown in the UI.
        description: Prose description (not shown directly in-game).
        ambient:     Scene-setting lines (one chosen at random per visit).
        actions:     Static navigation and interaction options.
    """

    id: str
    name: str
    description: str
    ambient: list[str]
    actions: list[ActionData]


def parse_action_data(data: Any) -> ActionData:
    """Parse a single action entry from a location's actions array."""
    obj = ActionData()
    obj.line = data.get("line", "Do something...")
    obj.event = data["event"]
    return obj


def parse_location_data(data: Any) -> LocationData:
    """
    Parse a full location JSON dict into a LocationData object.

    Args:
        data: Parsed JSON dict from data/location/<id>.json.

    Returns:
        A LocationData with all fields populated.
        Falls back to [description] if ambient is missing.
    """
    obj = LocationData()
    obj.id = data["id"]
    obj.name = data["name"]
    obj.description = data["description"]
    obj.ambient = data.get("ambient", [obj.description])
    obj.actions = list(map(parse_action_data, data.get("actions", [])))
    return obj
