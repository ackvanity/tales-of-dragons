"""
librarians/hofferson/astrid.py — Character data parser.

Parses raw JSON dicts (loaded from data/character/human/) into typed
CharacterData objects consumed by clans/hofferson/astrid.py.
"""

from typing import Any


class ActionData:
    """
    Raw action entry parsed from a character's JSON actions array.

    Attributes:
        line:  Button label shown to the player.
        event: Event string to be parsed by librarians/evaluator.py.
    """

    line: str
    event: str


class CharacterVariableData:
    """
    Runtime properties of a character parsed from the JSON properties block.

    Attributes:
        health:           Starting health value.
        location:         Starting location ID.
        extra_variables:  Any additional properties not explicitly handled.
    """

    health: int
    location: str
    extra_variables: dict[str, str]


class CharacterData:
    """
    Fully parsed representation of a character JSON file.

    Attributes:
        id:          Unique identifier matching the filename.
        name:        Short display name.
        fullname:    Full name for prose and descriptions.
        description: Character bio.
        menu_lines:  Greeting lines (one chosen at random per visit).
        actions:     Static dialogue options (usually empty).
        variables:   Runtime properties (location, health, etc.).
    """

    id: str
    name: str
    fullname: str
    description: str
    menu_lines: list[str]
    actions: list[ActionData]
    variables: CharacterVariableData


def parse_variables_data(data: dict[str, Any]) -> CharacterVariableData:
    """
    Parse the properties block of a character JSON file.

    Pops known keys (health, location) from data and stores the remainder
    in extra_variables for forward compatibility.
    """
    obj = CharacterVariableData()
    obj.health = data.pop("health", 100)
    obj.location = data.pop("location")
    obj.extra_variables = data
    return obj


def parse_action_data(data: Any) -> ActionData:
    """Parse a single action entry from a character's actions array."""
    obj = ActionData()
    obj.line = data.get("line", "Do something...")
    obj.event = data["event"]
    return obj


def parse_character_data(data: Any) -> CharacterData:
    """
    Parse a full character JSON dict into a CharacterData object.

    Args:
        data: Parsed JSON dict from data/character/human/<id>.json.

    Returns:
        A CharacterData with all fields populated.
    """
    obj = CharacterData()
    obj.id = data["id"]
    obj.name = data["name"]
    obj.fullname = data["fullname"]
    obj.description = data["description"]
    obj.menu_lines = data.get("menu_lines", ["Hey there!"])
    obj.actions = list(map(parse_action_data, data.get("actions", [])))
    obj.variables = parse_variables_data(data.get("properties", {}))
    return obj
