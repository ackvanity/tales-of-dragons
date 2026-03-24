"""
clans/hofferson/astrid.py — NPC dialogue system.

Manages Human entities (NPCs) and the Talking state (the dialogue screen
shown when the player interacts with an NPC).

Key responsibilities:
  - Loading NPC data from data/character/human/<id>.json
  - Tracking dynamically injected dialogue options (from quest hooks)
  - Dispatching HumanInteract events to enter/exit dialogue
  - Rendering the Talking state via TalkingRenderCommand
"""

import haddock
from librarians.hofferson import astrid
from librarians import core
from clans.hofferson import Action
import random

modules = []
"""
Registered modules that inject extra character actions into all NPC menus.

Populated at startup by main.py via modules.append(). Each entry must
expose an extra_character_actions: list[Action] attribute.
"""


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class HumanInteractEventBase:
    """Shared payload for human interaction events."""

    to: str

    def __init__(self, to: str) -> None:
        self.to = to


class HumanInteractEngineEvent(HumanInteractEventBase, haddock.EngineEvent):
    """
    Engine event that pushes a Talking state for the given NPC.

    Handled by HumanInteractRider. Fired when the player selects an NPC
    from a location menu, or when a quest directly triggers an interaction.
    """

    @staticmethod
    def tag() -> str:
        return "hofferson.HumanInteractEngineEvent"

    def _serialize_payload(self) -> haddock.JSONValue:
        return self.to

    @classmethod
    def deserialize(cls, data: haddock.JSONValue) -> "HumanInteractEngineEvent":  # type: ignore
        if not isinstance(data, str):
            raise haddock.DeserializeException(f"Expected str for HumanInteractEngineEvent, got {data!r}")
        return cls(data)


class HumanInteractEvent(HumanInteractEventBase, haddock.Event):
    """
    Non-engine variant of HumanInteractEngineEvent.

    Fired by TalkingRider when the player interacts with an NPC while
    already in a Talking state (i.e. switching conversation target).
    """


class AddDialogueEvent(haddock.EngineEvent):
    """
    Engine event that injects a dialogue option into an NPC's menu.

    Fired by DragonicQuest via add_character_hook(). Handled by
    AddDialogueEventRider, which ensures the Human entity exists before
    forwarding as a BaseAddDialogueEvent.
    """

    character: str
    line: str
    event: haddock.Event
    id: str

    def __init__(self, character: str, line: str, event: haddock.Event, id: str) -> None:
        self.character = character
        self.line = line
        self.event = event
        self.id = id


class BaseAddDialogueEvent(haddock.Event):
    """
    Non-engine variant of AddDialogueEvent, broadcast to entity riders.

    HumanRider picks this up and appends the action to the target Human's
    extra_character_actions list.
    """

    character: str
    line: str
    event: haddock.Event
    id: str

    def __init__(self, character: str, line: str, event: haddock.Event, id: str) -> None:
        self.character = character
        self.line = line
        self.event = event
        self.id = id


class RemoveDialogueEvent(haddock.Event):
    """
    Removes a previously injected dialogue option from an NPC.

    Fired automatically when the player clicks a quest-injected action,
    so the option disappears after one use.
    """

    character: str
    id: str

    def __init__(self, character: str, id: str) -> None:
        self.character = character
        self.id = id

    @staticmethod
    def tag() -> str:
        return "hofferson.RemoveDialogueEvent"

    def _serialize_payload(self) -> haddock.JSONValue:
        return {"character": self.character, "id": self.id}

    @classmethod
    def deserialize(cls, data: haddock.JSONValue) -> "RemoveDialogueEvent":  # type: ignore
        if not isinstance(data, dict):
            raise haddock.DeserializeException(f"Expected dict for RemoveDialogueEvent, got {data!r}")
        return cls(data["character"], data["id"])  # type: ignore


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class Human(haddock.Entity):
    """
    An interactable NPC loaded from data/character/human/<id>.json.

    Stored in Hiccup.entities as EntityID("hofferson", "human", <id>).
    Created lazily on first interaction via get_human().

    Attributes:
        id:                       JSON id field, matches the file name.
        name:                     Short display name shown in dialogue.
        health:                   Current health (default 100).
        location:                 Current location ID.
        extra_character_actions:  Dynamically injected actions from quest hooks.
    """

    id: str
    name: str
    health: int
    location: str
    extra_character_actions: list[Action]

    def __init__(self, id: str) -> None:
        self.id = id
        data = astrid.parse_character_data(core.get_data(f"character/human/{id}"))
        self.name = data.name
        self.health = data.variables.health
        self.location = data.variables.location
        self.extra_character_actions = []

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return {
            "id": self.id,
            "name": self.name,
            "health": self.health,
            "location": self.location,
            "extra_character_actions": [a.serialize() for a in self.extra_character_actions],
        }

    @classmethod
    def _deserialize(cls: type["Human"], data: haddock.JSONValue, version: int) -> "Human":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict for Human, got {data!r}")
            obj = cls(data["id"])  # type: ignore
            obj.health = data["health"]  # type: ignore
            obj.location = data["location"]  # type: ignore
            obj.extra_character_actions = [
                Action.deserialize(a) for a in data.get("extra_character_actions", [])  # type: ignore
            ]
            return obj
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "hofferson.Human"

    @property
    def actions(self) -> list[Action]:
        """Return the NPC's static actions (currently just a Goodbye option)."""
        return [Action(line=f"Goodbye {self.name}", signal=haddock.PopStateEvent())]

    @property
    def line(self) -> str:
        """Return a random greeting line from the NPC's menu_lines."""
        data = astrid.parse_character_data(core.get_data(f"character/human/{self.id}"))
        return random.choice(data.menu_lines)


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

class Talking(haddock.State):
    """
    Active state while the player is in conversation with an NPC.

    Holds the ID of the NPC being spoken to. Rendered by TalkingRider
    into a TalkingRenderCommand consumed by TalkingRenderChief.
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
    def _deserialize(cls: type["Talking"], data: haddock.JSONValue, version: int) -> "Talking":
        if version == 1:
            if not isinstance(data, str):
                raise haddock.DeserializeException(f"Expected str for Talking.to, got {data!r}")
            return cls(data)
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "hofferson.Talking"


# ---------------------------------------------------------------------------
# Render command
# ---------------------------------------------------------------------------

class TalkingRenderCommand(haddock.RenderCommand):
    """
    Data passed from TalkingRider to TalkingRenderChief.

    Attributes:
        speaker:  NPC display name.
        line:     Greeting line shown above the action menu.
        actions:  Full list of selectable options (static + injected + module).
    """

    speaker: str
    line: str
    actions: list[Action]

    def __init__(self, speaker: str, line: str, actions: list[Action]) -> None:
        self.speaker = speaker
        self.line = line
        self.actions = actions


# ---------------------------------------------------------------------------
# Riders
# ---------------------------------------------------------------------------

class HumanInteractRider(haddock.EventRider[HumanInteractEngineEvent]):
    """Intercepts HumanInteractEngineEvent and pushes a Talking state."""

    event_type = HumanInteractEngineEvent

    def roll_call(self, event: HumanInteractEngineEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Talking(event.to)))


class AddDialogueEventRider(haddock.EventRider[AddDialogueEvent]):
    """
    Intercepts AddDialogueEvent, ensures the Human entity exists,
    then re-broadcasts as BaseAddDialogueEvent for HumanRider to handle.
    """

    event_type = AddDialogueEvent

    def roll_call(self, event: AddDialogueEvent) -> None:
        get_human(event.character)
        haddock.chieftain.mail_event(
            BaseAddDialogueEvent(event.character, event.line, event.event, event.id)
        )


class HumanRider(haddock.EntityRider[Human]):
    """
    Handles events for all Human entities.

    Listens for BaseAddDialogueEvent to inject quest actions, and
    RemoveDialogueEvent to remove them after use.
    """

    entity_type = Human

    def roll_call(self, entity: Human, event: haddock.Event) -> None:
        if isinstance(event, BaseAddDialogueEvent):
            print(f"Trying to add a line to {event.character} - now at {entity.id}")
        if isinstance(event, BaseAddDialogueEvent) and event.character == entity.id:
            print("Adding line!")
            entity.extra_character_actions.append(Action(
                line=event.line,
                signal=event.event,
                id=event.id,
            ))
        if isinstance(event, RemoveDialogueEvent) and event.character == entity.id:
            entity.extra_character_actions = [
                a for a in entity.extra_character_actions if a.id != event.id
            ]


class TalkingRider(haddock.StateRider[Talking]):
    """Handles events and renders the Talking state."""

    state_type = Talking

    def roll_call(self, state: Talking, event: haddock.Event) -> None:
        if isinstance(event, HumanInteractEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())
            haddock.chieftain.mail_event(HumanInteractEngineEvent(event.to))

    def render(self, state: Talking) -> haddock.RenderCommand:
        """Build a TalkingRenderCommand from the NPC's combined action list."""
        character = get_human(state.to)

        actions: list[Action] = []
        actions += character.actions
        actions += character.extra_character_actions
        for module in modules:
            actions += module.extra_character_actions

        return TalkingRenderCommand(character.name, character.line, actions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_human(name: str) -> Human:
    """
    Return the Human entity for the given NPC id, creating it if absent.

    Stored as EntityID("hofferson", "human", name).
    """
    return haddock.chieftain.call_entity(
        haddock.EntityID("hofferson", "human", name),
        lambda: Human(name),
    )  # type: ignore


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

riders: haddock.Riders = [HumanRider(), TalkingRider(), HumanInteractRider(), AddDialogueEventRider()]
chiefs: haddock.Chiefs = []

# Register all events that appear as Action.signal or inside EventSeries
haddock.register_event(HumanInteractEngineEvent)
haddock.register_event(RemoveDialogueEvent)

# Register serializable types with the engine type registries
haddock.register_state(Talking)
haddock.register_entity(Human)
