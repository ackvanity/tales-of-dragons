from typing import Any


class ActionData:
    line: str
    event: str

class CharacterVariableData:
    health: int
    location: str
    extra_variables: dict[str, str]

class CharacterData:
    id: str
    name: str
    fullname: str
    description: str
    menu_lines: list[str]
    actions: list[ActionData]
    variables: CharacterVariableData

def parse_variables_data(data: dict[str, Any]) -> CharacterVariableData:
    obj = CharacterVariableData()

    obj.health = data.pop("health", 100)
    obj.location = data.pop("location")
    obj.extra_variables = data

    return obj

def parse_action_data(data: Any) -> ActionData:
    obj = ActionData()

    obj.line = data.get("line", "Do something...")
    obj.event = data["event"]

    return obj


def parse_character_data(data: Any) -> CharacterData:
    obj = CharacterData()

    obj.id = data["id"]
    obj.name = data["name"]
    obj.fullname = data["fullname"]
    obj.description = data["description"]
    obj.menu_lines = data.get("menu_lines", "Hey there!")
    obj.actions = list(map(parse_action_data, data.get("actions", [])))
    obj.variables = parse_variables_data(data.get("properties", {}))

    return obj
