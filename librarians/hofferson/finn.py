from typing import Any

class ActionData:
    line: str
    event: str


class LocationData:
    id: str
    name: str
    description: str
    ambient: list[str]
    actions: list[ActionData]

def parse_action_data(data: Any) -> ActionData:
    obj = ActionData()

    obj.line = data.get("line", "Do something...")
    obj.event = data["event"]

    return obj

def parse_location_data(data: Any) -> LocationData:
    obj = LocationData()

    obj.id = data["id"]
    obj.name = data["name"]
    obj.description = data["description"]
    obj.ambient = data.get("ambient", [obj.description])
    obj.actions = list(map(parse_action_data, data.get("actions", [])))

    return obj