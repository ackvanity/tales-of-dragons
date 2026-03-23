"""
haddock.py — Engine core for Tales of Dragons.

Defines the fundamental building blocks of the game engine:
  - Serialization interface (Serializable, State, Entity, EntityID)
  - Event system (Event, EngineEvent, and built-in engine events)
  - Rider / Chief dispatch pattern (StateRider, EntityRider, EventRider, RenderChief)
  - Hiccup: the central engine runner that owns all game state

The engine follows an event-sourcing model: everything the player does
produces an Event, which is dispatched to registered riders that mutate
state, which in turn triggers a render pass through the active RenderChief.
"""

from typing import Callable, TypeAlias, TypeVar, Generic, Type, Union
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Type variables used for generic rider / serialization bounds
# ---------------------------------------------------------------------------

S = TypeVar("S", bound="State")
E = TypeVar("E", bound="Entity")
V = TypeVar("V", bound="EngineEvent")
C = TypeVar("C", bound="RenderCommand")
R = TypeVar("R", bound="Serializable")

# ---------------------------------------------------------------------------
# JSON type aliases
# ---------------------------------------------------------------------------

JSONValue = Union["JSONPrimitive", "JSONObject", "JSONArray"]
"""Any value that can be round-tripped through json.dumps / json.loads."""

JSONPrimitive = Union[str, int, float, bool, None]
JSONObject = dict[str, JSONValue]
JSONArray = list[JSONValue]


# ---------------------------------------------------------------------------
# Serialization interface
# ---------------------------------------------------------------------------

class Serializable(ABC):
    """
    Base interface for all objects that can be persisted to a save file.

    Implementors must provide:
      - serialize()   → a JSONValue (plain Python object, no custom classes)
      - deserialize() → reconstruct an instance from that JSONValue
      - tag()         → a globally unique string key for the type registry

    State and Entity provide a concrete serialize() / deserialize() that
    wrap the payload in [version, payload] — subclasses implement
    _serialize / _deserialize instead.
    """

    @abstractmethod
    def serialize(self) -> JSONValue: ...

    @classmethod
    @abstractmethod
    def deserialize(cls: Type[R], data: JSONValue) -> R: ...

    @staticmethod
    @abstractmethod
    def tag() -> str: ...


class State(Serializable):
    """
    A game screen or mode pushed onto Hiccup's state stack.

    The top of the stack is the active state. States are rendered each
    frame by their matching StateRider, which produces a RenderCommand
    consumed by a RenderChief.

    Subclasses must implement:
      - version      → int, increment when the serialized format changes
      - _serialize() → JSONValue payload (without version wrapper)
      - _deserialize(data, version) → reconstruct from payload
      - tag()        → globally unique string, e.g. "hofferson.Talking"
    """

    @property
    @abstractmethod
    def version(self) -> int: ...

    @abstractmethod
    def _serialize(self) -> JSONValue: ...

    @classmethod
    @abstractmethod
    def _deserialize(cls: Type[S], data: JSONValue, version: int) -> S: ...

    @staticmethod
    @abstractmethod
    def tag() -> str: ...

    def serialize(self) -> JSONValue:
        """Return [version, payload] suitable for storage."""
        return [self.version, self._serialize()]

    @classmethod
    def deserialize(cls: Type[S], data: JSONValue) -> S:
        """Reconstruct a State from [version, payload]. Raises DeserializeException on bad input."""
        if not isinstance(data, list) or len(data) < 2:
            raise DeserializeException(f"Expected [version, payload], got {data!r}")
        version = data[0]
        if not isinstance(version, int):
            raise DeserializeException(f"Expected int version, got {version!r}")
        return cls._deserialize(data[1], version)


class Entity(Serializable):
    """
    A persistent game object stored in Hiccup.entities, keyed by EntityID.

    Examples: Human NPCs, Locations, the Player, Satchels, DragonicQuests.

    Subclasses must implement:
      - version      → int, increment when the serialized format changes
      - _serialize() → JSONValue payload (without version wrapper)
      - _deserialize(data, version) → reconstruct from payload
      - tag()        → globally unique string, e.g. "hofferson.Human"
    """

    @property
    @abstractmethod
    def version(self) -> int: ...

    @abstractmethod
    def _serialize(self) -> JSONValue: ...

    @staticmethod
    @abstractmethod
    def tag() -> str: ...

    @classmethod
    @abstractmethod
    def _deserialize(cls: Type[E], data: JSONValue, version: int) -> E: ...

    def serialize(self) -> JSONValue:
        """Return [version, payload] suitable for storage."""
        return [self.version, self._serialize()]

    @classmethod
    def deserialize(cls: Type[E], data: JSONValue) -> E:
        """Reconstruct an Entity from [version, payload]. Raises DeserializeException on bad input."""
        if not isinstance(data, list) or len(data) < 2:
            raise DeserializeException(f"Expected [version, payload], got {data!r}")
        version = data[0]
        if not isinstance(version, int):
            raise DeserializeException(f"Expected int version, got {version!r}")
        return cls._deserialize(data[1], version)


@dataclass(frozen=True)
class EntityID(Serializable):
    """
    Immutable three-part key identifying an entity in Hiccup.entities.

    Convention:
      clan    — Python module clan name (e.g. "hofferson", "jorgenson")
      species — entity type within the clan (e.g. "human", "location", "player")
      name    — unique instance identifier (e.g. "hiccup", "berk_square", "player")

    The player entity is always stored as EntityID("jorgenson", "player", "player").
    """

    clan: str
    species: str
    name: str

    def __str__(self) -> str:
        return f"|Clan: {self.clan}|Species: {self.species}|Name: {self.name}|"

    @staticmethod
    def tag() -> str:
        return "haddock.EntityID"

    def serialize(self) -> JSONValue:
        """Return [clan, species, name] as a JSONArray."""
        return [self.clan, self.species, self.name]

    @classmethod
    def deserialize(cls, data: JSONValue) -> "EntityID":
        """Reconstruct an EntityID from [clan, species, name]."""
        if not isinstance(data, list) or len(data) < 3:
            raise DeserializeException(f"Expected [clan, species, name], got {data!r}")
        return cls(data[0], data[1], data[2])  # type: ignore


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class Event:
    """
    Base class for all game events.

    Plain Events are broadcast to EntityRiders and the active StateRider.
    """


class EngineEvent(Event):
    """
    An event intercepted by Hiccup or an EventRider before reaching state/entity riders.

    Use EngineEvents for actions that modify engine structure (push/pop states,
    trigger narrative sequences) rather than for in-world interactions.
    """


class PopStateEvent(EngineEvent):
    """Remove the top state from Hiccup's state stack."""


class AppendStateEvent(EngineEvent):
    """Push a new state onto Hiccup's state stack."""

    state: State

    def __init__(self, state: State) -> None:
        self.state = state


class HaddockEvent(Event):
    """Events emitted by the engine itself (not by game logic)."""


class TeamAssembled(HaddockEvent):
    """
    Fired once when the engine finishes its boot sequence.

    DragonicQuests listen for this event to start their coroutines on
    the first frame.
    """


class EventSeries(EngineEvent):
    """
    Wraps multiple events so they can be dispatched as a single unit.

    Useful when only one event is expected (e.g. a button signal) but
    several logical steps need to happen in sequence.

    Note: For repeated use, create a distinct EventSeries instance each
    time rather than mutating a shared one.
    """

    events: list[Event]

    def __init__(self, events: list[Event] | None = None) -> None:
        self.events = events if events is not None else []


# ---------------------------------------------------------------------------
# Application interface
# ---------------------------------------------------------------------------

class Application(ABC):
    """
    Abstract interface for the UI layer.

    Implemented by TextualApplication in stoick.py. RenderChiefs receive
    an Application instance and call these methods to mount widgets.
    """

    @abstractmethod
    def get_mount_point(self) -> object:
        """Return the root container widget that content is mounted into."""
        ...

    @abstractmethod
    def get_story(self) -> "State | None":
        """Return the active Story widget, or None if no Story is mounted."""
        ...


# ---------------------------------------------------------------------------
# Render pipeline
# ---------------------------------------------------------------------------

class RenderCommand:
    """
    Data transfer object produced by a StateRider and consumed by a RenderChief.

    Carries all information the View needs to render a state, with no
    knowledge of how it will be displayed.
    """


class RenderingException(Exception):
    """Raised when the render pipeline cannot find a rider or chief for the current state."""


# ---------------------------------------------------------------------------
# Serialization exceptions
# ---------------------------------------------------------------------------

class DeserializeException(Exception):
    """Raised when a serialized payload cannot be parsed."""


class DeserializeVersionUnsupportedException(DeserializeException):
    """Raised when the stored version number has no corresponding deserializer."""


# ---------------------------------------------------------------------------
# Rider / Chief interfaces
# ---------------------------------------------------------------------------

class StateRider(Generic[S], ABC):
    """
    Handles events and renders the state S while it is active.

    Registered with Hiccup via enroll_rider(). Only one StateRider per
    State type. The rider is called for the top-of-stack state only.
    """

    state_type: Type[S]

    @abstractmethod
    def render(self, state: S) -> RenderCommand:
        """Produce a RenderCommand representing the current visual state."""
        ...

    @abstractmethod
    def roll_call(self, state: S, event: Event) -> None:
        """React to an event while this state is active."""
        ...


class EntityRider(Generic[E], ABC):
    """
    Handles events for all active entities of type E.

    Every entity of the matching type receives the roll_call for every
    non-EngineEvent, regardless of which state is active.
    """

    entity_type: Type[E]

    @abstractmethod
    def roll_call(self, entity: E, event: Event) -> None:
        """React to an event on behalf of a specific entity instance."""
        ...


class EventRider(Generic[V], ABC):
    """
    Intercepts a specific EngineEvent type before it reaches state/entity riders.

    Use for global engine-level reactions (e.g. pushing a new state in
    response to a navigation event).
    """

    event_type: Type[V]

    @abstractmethod
    def roll_call(self, event: V) -> None:
        """Handle the engine event."""
        ...


class RenderChief(Generic[C], ABC):
    """
    Translates a RenderCommand of type C into UI widgets.

    Lives in the components/ layer (View), not in clans/ (Controller).
    Registered with Hiccup via declare_chief().
    """

    command_type: Type[C]

    @abstractmethod
    def render(self, command: C, application) -> None:
        """Mount widgets into the application based on the render command."""
        ...


# ---------------------------------------------------------------------------
# Test stub
# ---------------------------------------------------------------------------

class TestApplication(Application):
    """Minimal Application implementation for use in tests and debugging."""

    def get_mount_point(self) -> object:
        return None

    def get_story(self) -> "State | None":
        return None

    def clear_screen(self) -> None:
        print("Screen cleared")

    def present_state(self, state: State) -> None:
        print("State sent to render:")
        print(state)


# ---------------------------------------------------------------------------
# Engine runner
# ---------------------------------------------------------------------------

class Hiccup:
    """
    The central game engine singleton, accessed via haddock.chieftain.

    Owns the state stack, entity registry, event queue, and all registered
    riders and chiefs. Drives the game loop by dispatching events and
    triggering render passes.

    Typical usage in main.py:
        haddock.chieftain = haddock.Hiccup()
        haddock.chieftain.application = stoick.TextualApplication()
        haddock.chieftain.register_clan(astrid)
        haddock.chieftain.declare_chief(TalkingRenderChief())
        haddock.chieftain.application.run()
    """

    def __init__(self) -> None:
        self.states: list[State] = []
        """Stack of active states. The last element is the current screen."""

        self.entities: dict[EntityID, Entity] = {}
        """All persistent game objects, keyed by EntityID."""

        self.event_queue: deque[Event] = deque()
        """FIFO queue of pending events. Drained completely before each render."""

        self.render_chiefs: list[RenderChief] = []
        """All registered render chiefs, searched by command_type on each render."""

        self.state_riders: list[StateRider] = []
        """Riders dispatched for the active (top-of-stack) state."""

        self.entity_riders: list[EntityRider] = []
        """Riders dispatched for all matching entities on every non-engine event."""

        self.event_riders: list[EventRider] = []
        """Riders that intercept specific EngineEvent types globally."""

        self.application: object = None
        """The active Application (UI layer). Set before calling run()."""

        self._in_event_loop: bool = False
        """Re-entrancy guard: prevents nested dispatch loops."""

    def render(self) -> None:
        """
        Render the current (top-of-stack) state via its StateRider and RenderChief.

        Exits the process if the state stack is empty (game over).
        Raises RenderingException if no rider or chief is registered for the state.
        """
        if not len(self.states):
            exit(0)

        state = self.states[-1]

        for rider in self.state_riders:
            if isinstance(state, rider.state_type):
                command = rider.render(state)

                for chief in self.render_chiefs:
                    if isinstance(command, chief.command_type):
                        chief.render(command, self.application)
                        return

                raise RenderingException(
                    f"No chief took command {command}. Perhaps you should learn diplomacy..."
                )

        raise RenderingException(
            f"Fishlegs needed to ask about state {state} but no rider was assigned. "
            f"Try talking to Hiccup and Astrid about the team formation..."
        )

    def _dispatch_events(self) -> None:
        """
        Drain the event queue, calling render() after each full drain.

        Re-entrant safe: if a render triggers more events, they are processed
        in the next inner loop iteration.
        """
        if self._in_event_loop:
            return

        self._in_event_loop = True
        while len(self.event_queue):  # Renders may raise events!
            while len(self.event_queue):
                self.__dispatch_event_loop__(self.event_queue[0])
                self.event_queue.popleft()
            self.render()
        self._in_event_loop = False

    def __dispatch_event_loop__(self, event: Event) -> None:
        """
        Dispatch a single event to the appropriate riders.

        EngineEvents are handled by EventRiders or Hiccup itself (pop/push/series).
        Non-engine events are broadcast to all EntityRiders, then to the active StateRider.
        """
        print(f"Got new event {event}")

        if isinstance(event, EngineEvent):
            for rider in self.event_riders:
                if isinstance(event, rider.event_type):
                    rider.roll_call(event)
                    return

            if isinstance(event, PopStateEvent):
                self.states.pop()
                return

            if isinstance(event, AppendStateEvent):
                self.states.append(event.state)
                return

            if isinstance(event, EventSeries):
                for next_event in event.events:
                    self.mail_event(next_event)
                return

            raise RenderingException(
                f"Astrid did a roll call to brief about event {event} to the Riders, "
                f"but nobody came. Please ask Hiccup to assign *someone* here. "
                f"Oh, and she wants it done, fast!"
            )

        if not len(self.states):
            raise RenderingException(
                f"A Terrible Terror carrying a mail about {event} landed at house Haddock, "
                f"but nobody was there! You should find Hiccup and make sure he's not captured again..."
            )

        for entity in self.entities.values():
            for rider in self.entity_riders:
                if isinstance(entity, rider.entity_type):
                    rider.roll_call(entity, event)

        for rider in self.state_riders:
            if isinstance(self.states[-1], rider.state_type):
                rider.roll_call(self.states[-1], event)
                return

        raise RenderingException(
            f"Astrid did a roll call to brief about event {event} on state {self.states[-1]}, "
            f"but nobody came. Please ask Hiccup to assign *someone* here. "
            f"Oh, and she wants it done, fast!"
        )

    def mail_event(self, event: Event) -> None:
        """
        Queue an event and trigger dispatch.

        This is the primary entry point for all game logic. Called by riders,
        components, and quest scripts to drive state changes.
        """
        print(f"Sending a Terrible Terror to tell {event}...")
        self.event_queue.append(event)
        self._dispatch_events()

    def enroll_rider(self, rider: "StateRider | EntityRider | EventRider") -> None:
        """Register a rider. Called automatically by register_clan()."""
        if isinstance(rider, StateRider):
            self.state_riders.append(rider)
        if isinstance(rider, EntityRider):
            self.entity_riders.append(rider)
        if isinstance(rider, EventRider):
            self.event_riders.append(rider)

    def declare_chief(self, chief: RenderChief) -> None:
        """Register a render chief. Must be called explicitly in main.py."""
        self.render_chiefs.append(chief)

    def register_clan(self, clan) -> None:
        """
        Register all riders and chiefs exported by a clan module.

        Expects the module to expose:
          clan.riders: list[StateRider | EntityRider | EventRider]
          clan.chiefs: list[RenderChief]
        """
        for rider in clan.riders:
            self.enroll_rider(rider)
        for chief in clan.chiefs:
            self.declare_chief(chief)
        print(
            f"Clan {clan.__name__} has officially moved to Berk! "
            f"The entire village celebrates a new ally to defend all of our dragons."
        )

    def call_entity(
        self,
        position: EntityID,
        default: Callable[[], Entity] | None = None,
    ) -> Entity:
        """
        Fetch an entity by ID, optionally creating it if absent.

        Args:
            position: The EntityID key to look up.
            default:  Zero-argument callable that constructs the entity if missing.
                      If None and the entity is absent, raises KeyError.
        """
        if position in self.entities:
            return self.entities[position]
        elif default is not None:
            return self.entities.setdefault(position, default())
        else:
            raise KeyError(position)

    def call_entities(
        self,
        clan: str | None = None,
        species: str | None = None,
        name: str | None = None,
    ) -> list[tuple[EntityID, Entity]]:
        """
        Return all entities whose EntityID matches the given partial filter.

        Any parameter left as None is treated as a wildcard.
        Returns a list of (EntityID, Entity) tuples.
        """
        return [
            (k, v)
            for k, v in self.entities.items()
            if (clan is None or k.clan == clan)
            and (species is None or k.species == species)
            and (name is None or k.name == name)
        ]


# ---------------------------------------------------------------------------
# Module-level type aliases and singleton
# ---------------------------------------------------------------------------

Riders: TypeAlias = list[EventRider | StateRider | EntityRider]
"""Type alias for the riders list exported by each clan module."""

Chiefs: TypeAlias = list[RenderChief]
"""Type alias for the chiefs list exported by each clan module."""

chieftain: Hiccup = None  # type: ignore
"""
The global engine singleton. Assigned in main.py before the app runs.

The player EntityID is always EntityID("jorgenson", "player", "player").
"""
