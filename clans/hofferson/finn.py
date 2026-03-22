import copy
import haddock
import librarians.hofferson.finn as librarian
from librarians import core, evaluator
from librarians.hofferson import get_humans
import random
from clans.hofferson import astrid

modules = []


class LocationTeleportEventBase:
    to: str

    def __init__(self, to: str):
        self.to = to


class LocationTeleportEngineEvent(LocationTeleportEventBase, haddock.EngineEvent):
    pass


class LocationTeleportEvent(LocationTeleportEventBase, haddock.Event):
    pass


class LocationTeleportRider(haddock.EventRider[LocationTeleportEngineEvent]):
    event_type = LocationTeleportEngineEvent

    def roll_call(self, event: LocationTeleportEngineEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Wandering(event.to)))


class LocationAction:
    @property
    def line(self) -> str: ...

    condition: str
    signal: haddock.Event


class LiteralLocationAction(LocationAction):
    _line: str

    @property
    def line(self) -> str:
        return self._line

    @line.setter
    def line(self, line: str) -> None:
        self._line = line

    condition: str = "True"


class Location(haddock.Entity):
    extra_actions: list[LocationAction]

    def __init__(self, id):
        self.extra_actions = []
        self.id = id

    def interpret_action(self, action: LocationAction) -> LiteralLocationAction:
        return action # type: ignore

    @property
    def actions(self) -> list[LiteralLocationAction]:
        actions = librarian.parse_location_data(core.get_data(f"location/{self.id}")).actions
        action_list: list[LocationAction] = list(self.extra_actions)
        for action in actions:
            action_obj = LiteralLocationAction()
            action_obj.line = action.line
            action_obj.signal = evaluator.parse_event(action.event)
            action_obj.condition = "True"
            action_list.append(action_obj)
        for human in get_humans():
            character = astrid.get_human(human)
            print("Checking human", character.name, "residing at", character.location, "while we are at", self.id)
            if character.location == self.id:
                action_obj = LiteralLocationAction()
                action_obj.line = f"Hi there {character.name}!"
                action_obj.signal = astrid.HumanInteractEngineEvent(character.id)
                action_list.append(action_obj)
        return list(map(self.interpret_action, action_list))

    @property
    def ambient(self) -> str:
        return random.choice(librarian.parse_location_data(core.get_data(f"location/{self.id}")).ambient)


class Wandering(haddock.State):
    to: str

    def __init__(self, to: str):
        self.to = to
    
    @property
    def version(self) -> int:
        return 1
    
    def _serialize(self) -> str:
        return self.to
    
    @classmethod
    def _deserialize(cls: type["Wandering"], data: str, version: int) -> "Wandering":
        return cls(data)


class WanderingRenderCommand(haddock.RenderCommand):
    id: str
    line: str
    actions: list[LiteralLocationAction]

    def __init__(self, id: str, line: str, actions: list[LiteralLocationAction]):
        self.id = id
        self.line = line
        self.actions = actions


class LocationRider(haddock.EntityRider[Location]):
    entity_type = Location

    def roll_call(self, entity: Location, event: haddock.Event) -> None:
        pass


class WanderingRider(haddock.StateRider[Wandering]):
    state_type = Wandering

    def roll_call(self, state: Wandering, event: haddock.Event) -> None:
        if isinstance(event, LocationTeleportEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())
            haddock.chieftain.mail_event(LocationTeleportEngineEvent(event.to))

    def render(self, state: Wandering) -> haddock.RenderCommand:
        location = get_location(state.to)

        actions = copy.deepcopy(location.actions)
        for module in modules:
            for action in module.extra_character_actions:
                actions.append(action)

        return WanderingRenderCommand(state.to, location.ambient, actions)


class WanderingRenderChief(haddock.RenderChief[WanderingRenderCommand]):
    command_type = WanderingRenderCommand

    def render(self, command: WanderingRenderCommand, application) -> None:
        render_state = {
            "location": command.id,
            "ambient": command.line,
            "actions": [
                {"line": action.line, "signal": action.signal}
                for action in command.actions
            ],
        }

        application.send_location(render_state)

def get_location(id: str) -> Location:
    return haddock.chieftain.call_entity(haddock.EntityID("hofferson", "location", id), lambda: Location(id))  # type: ignore


riders: haddock.Riders = [LocationRider(), WanderingRider(), LocationTeleportRider()]
chiefs: haddock.Chiefs = [WanderingRenderChief()]
