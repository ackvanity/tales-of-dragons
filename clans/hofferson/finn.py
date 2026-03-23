"""
clans/hofferson/finn.py — Location and navigation system.

Manages Location entities (map nodes) and the Wandering state (the
exploration screen shown when the player is moving around the world).

Key responsibilities:
  - Loading location data from data/location/<id>.json
  - Synthesizing per-location action lists (navigation + present NPCs)
  - Dispatching LocationTeleport events to move between locations
  - Rendering the Wandering state via WanderingRenderCommand
"""

import haddock
import librarians.hofferson.finn as librarian
from librarians import core, evaluator
from librarians.hofferson import get_humans
from clans.hofferson import Action
import random
from clans.hofferson import astrid

modules = []
"""
Registered modules that inject extra location actions into all location menus.

Populated at startup by main.py via modules.append(). Each entry must
expose an extra_character_actions: list[Action] attribute.

Note: The attribute is named extra_character_actions on modules even when
injected into location menus, for consistency with the module protocol.
"""


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class LocationTeleportEventBase:
    """Shared payload for location teleport events."""

    to: str

    def __init__(self, to: str) -> None:
        self.to = to


class LocationTeleportEngineEvent(LocationTeleportEventBase, haddock.EngineEvent):
    """
    Engine event that pushes a Wandering state for the target location.

    Handled by LocationTeleportRider. Fired from location action menus
    (parsed from data/location/ JSON) or directly by quest scripts.
    """


class LocationTeleportEvent(LocationTeleportEventBase, haddock.Event):
    """
    Non-engine variant of LocationTeleportEngineEvent.

    Fired by WanderingRider when the player selects a travel action while
    already in a Wandering state.
    """


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class Location(haddock.Entity):
    """
    A map node loaded from data/location/<id>.json.

    Stored in Hiccup.entities as EntityID("hofferson", "location", <id>).
    Created lazily on first visit via get_location().

    The actions property dynamically builds the full action list each render
    by combining:
      1. extra_location_actions (injected at runtime, e.g. by quests)
      2. Static navigation actions from the location JSON file
      3. Greeting actions for any NPC currently present in this location

    Attributes:
        id:                     Location identifier matching the JSON filename.
        extra_location_actions: Runtime-injected actions (currently unused but reserved).
    """

    extra_location_actions: list[Action]

    def __init__(self, id: str) -> None:
        self.extra_location_actions = []
        self.id = id

    @property
    def actions(self) -> list[Action]:
        """
        Build the full action list for this location.

        Combines extra_location_actions, static JSON actions, and greeting
        actions for any NPC currently present here.
        """
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
        """Return a random ambient description line for this location."""
        return random.choice(
            librarian.parse_location_data(core.get_data(f"location/{self.id}")).ambient
        )


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

class Wandering(haddock.State):
    """
    Active state while the player is exploring a location.

    Holds the ID of the current location. Rendered by WanderingRider
    into a WanderingRenderCommand consumed by WanderingRenderChief.
    """

    to: str

    def __init__(self, to: str) -> None:
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

    @staticmethod
    def tag() -> str:
        return "hofferson.Wandering"


# ---------------------------------------------------------------------------
# Render command
# ---------------------------------------------------------------------------

class WanderingRenderCommand(haddock.RenderCommand):
    """
    Data passed from WanderingRider to WanderingRenderChief.

    Attributes:
        id:       Current location ID.
        ambient:  Scene-setting description shown to the player.
        actions:  Full list of selectable navigation and interaction options.
    """

    id: str
    ambient: str
    actions: list[Action]

    def __init__(self, id: str, ambient: str, actions: list[Action]) -> None:
        self.id = id
        self.ambient = ambient
        self.actions = actions


# ---------------------------------------------------------------------------
# Riders
# ---------------------------------------------------------------------------

class LocationRider(haddock.EntityRider[Location]):
    """Entity rider for Location. Currently a no-op placeholder."""

    entity_type = Location

    def roll_call(self, entity: Location, event: haddock.Event) -> None:
        pass


class LocationTeleportRider(haddock.EventRider[LocationTeleportEngineEvent]):
    """Intercepts LocationTeleportEngineEvent and pushes a Wandering state."""

    event_type = LocationTeleportEngineEvent

    def roll_call(self, event: LocationTeleportEngineEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Wandering(event.to)))


class WanderingRider(haddock.StateRider[Wandering]):
    """Handles events and renders the Wandering state."""

    state_type = Wandering

    def roll_call(self, state: Wandering, event: haddock.Event) -> None:
        if isinstance(event, LocationTeleportEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())
            haddock.chieftain.mail_event(LocationTeleportEngineEvent(event.to))

    def render(self, state: Wandering) -> haddock.RenderCommand:
        """Build a WanderingRenderCommand from the location's combined action list."""
        location = get_location(state.to)

        actions: list[Action] = list(location.actions)
        for module in modules:
            actions += module.extra_character_actions

        return WanderingRenderCommand(state.to, location.ambient, actions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_location(id: str) -> Location:
    """
    Return the Location entity for the given location id, creating it if absent.

    Stored as EntityID("hofferson", "location", id).
    """
    return haddock.chieftain.call_entity(
        haddock.EntityID("hofferson", "location", id),
        lambda: Location(id),
    )  # type: ignore


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

riders: haddock.Riders = [LocationRider(), WanderingRider(), LocationTeleportRider()]
chiefs: haddock.Chiefs = []
