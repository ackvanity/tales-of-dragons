import haddock
import librarians.hofferson.finn as librarian
from librarians import core, evaluator
from librarians.hofferson import get_humans
from clans.hofferson import Action
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


class Location(haddock.Entity):
    extra_location_actions: list[Action]

    def __init__(self, id):
        self.extra_location_actions = []
        self.id = id

    @property
    def actions(self) -> list[Action]:
        action_list: list[Action] = list(self.extra_location_actions)
        for action in librarian.parse_location_data(core.get_data(f"location/{self.id}")).actions:
            action_list.append(Action(
                line=action.line,
                signal=evaluator.parse_event(action.event),
            ))
        for human in get_humans():
            character = astrid.get_human(human)
            if character.location == self.id:
                action_list.append(Action(
                    line=f"Hi there {character.name}!",
                    signal=astrid.HumanInteractEngineEvent(character.id),
                ))
        return action_list

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
    
    def _serialize(self) -> haddock.JSONValue:
        return self.to

    @classmethod
    def _deserialize(cls: type["Wandering"], data: haddock.JSONValue, version: int) -> "Wandering":
        if not isinstance(data, str):
            raise haddock.DeserializeException(f"Expected str for Wandering.to, got {data!r}")
        return cls(data)


class WanderingRenderCommand(haddock.RenderCommand):
    id: str
    ambient: str
    actions: list[Action]

    def __init__(self, id: str, ambient: str, actions: list[Action]):
        self.id = id
        self.ambient = ambient
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

        actions: list[Action] = list(location.actions)
        for module in modules:
            actions += module.extra_character_actions

        return WanderingRenderCommand(state.to, location.ambient, actions)


def get_location(id: str) -> Location:
    return haddock.chieftain.call_entity(haddock.EntityID("hofferson", "location", id), lambda: Location(id))  # type: ignore


riders: haddock.Riders = [LocationRider(), WanderingRider(), LocationTeleportRider()]
chiefs: haddock.Chiefs = []
