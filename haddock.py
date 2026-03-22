from typing import Callable, TypeAlias, TypeVar, Generic, Type
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import json

S = TypeVar("S", bound="State")
E = TypeVar("E", bound="Entity")
V = TypeVar("V", bound="EngineEvent")
C = TypeVar("C", bound="RenderCommand")
R = TypeVar("R", bound="Serializable")

class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def deserialize(cls: Type[R], data: str) -> R:
        pass
    
    @staticmethod
    @abstractmethod
    def tag() -> str:
        pass

class State(Serializable):
    @property
    @abstractmethod
    def version(self) -> int:
        pass

    @abstractmethod
    def _serialize(self) -> str:
        return ""

    @classmethod
    @abstractmethod
    def _deserialize(cls: Type[S], data: str, version: int) -> S:
        pass

    def serialize(self) -> str:
        return json.dumps([self.version, self._serialize()])
    
    @classmethod
    def deserialize(cls: Type[S], data: str) -> S:
        obj = json.loads(data)
        return cls._deserialize(obj[1], obj[0])


class Entity(ABC):
    @property
    @abstractmethod
    def version(self) -> int:
        pass

    @abstractmethod
    def _serialize(self) -> str:
        return ""
    
    @staticmethod
    @abstractmethod
    def tag() -> str:
        pass

    @classmethod
    @abstractmethod
    def _deserialize(cls: Type[E], data: str, version: int) -> E:
        pass

    def serialize(self) -> str:
        return json.dumps([self.version, self._serialize()])
    
    @classmethod
    def deserialize(cls: Type[E], data: str) -> E:
        obj = json.loads(data)
        return cls._deserialize(obj[1], obj[0])

@dataclass(frozen=True)
class EntityID:
    clan: str
    species: str
    name: str

    def __str__(self):
        return f"|Clan: {self.clan}|Species: {self.species}|Name: {self.name}|"

    def serialize(self) -> str:
        return json.dumps([self.clan, self.species, self.name])

    @classmethod
    def deserialize(cls, data: str) -> "EntityID":
        lst = json.loads(data)
        id = cls(lst[0], lst[1], lst[2])
        return id

class Event:
    pass


class Application:
    pass


class RenderCommand:
    pass


class RenderingException(Exception):
    pass

# Errors while deserializing
class DeserializeException(Exception):
    pass

# The serialized save version cannot be deserialized
class DeserializeVersionUnsupportedException(DeserializeException):
    pass

# Events to be handled by event riders and/or the Haddocks
class EngineEvent(Event):
    pass

class PopStateEvent(EngineEvent):
    pass


class AppendStateEvent(EngineEvent):
    state: State

    def __init__(self, state: State):
        self.state = state

# Events sent by the Haddocks
class HaddockEvent(Event):
    pass

# Mailed when the engine is running
class TeamAssembled(HaddockEvent):
    pass


class StateRider(Generic[S], ABC):
    state_type: Type[S]

    @abstractmethod
    def render(self, state: S) -> RenderCommand: ...

    @abstractmethod
    def roll_call(self, state: S, event: Event) -> None: ...


class EntityRider(Generic[E], ABC):
    entity_type: Type[E]

    @abstractmethod
    def roll_call(self, entity: E, event: Event) -> None: ...


class EventRider(Generic[V], ABC):
    event_type: Type[V]

    @abstractmethod
    def roll_call(self, event: V) -> None: ...


class RenderChief(Generic[C], ABC):
    command_type: Type[C]

    @abstractmethod
    def render(self, command: C, application) -> None: ...


class TestApplication(Application):
    def clear_screen(self):
        print("Screen cleared")

    def present_state(self, state):
        print("State sent to render:")
        print(state)

# Dispatches multiple events in one batch
# Used to send multiple events when only one is expected
# For repeated use, a distinct event object is highly recommended
class EventSeries(EngineEvent):
    events: list[Event]

    def __init__(self, events=None):
        if events is None:
            events = []
        
        self.events = events

class Hiccup:
    def __init__(self):
        self.states: list[State] = []
        self.entities: dict[EntityID, Entity] = {}

        self.event_queue: deque[Event] = deque()

        self.render_chiefs: list[RenderChief] = []

        # Non-engine event handlers are set per *entity/state type* and not per *event type*
        self.state_riders: list[StateRider] = []
        self.entity_riders: list[EntityRider] = []
        # Global/engine/module events
        self.event_riders: list[EventRider] = []

        self.application: object = None

        self._in_event_loop: bool = False

    def render(self):
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
            f"Fishlegs needed to ask about state {state} but no rider was assigned. Try talking to Hiccup and Astrid about the team formation..."
        )

    def _dispatch_events(self):
        if self._in_event_loop:
            return

        self._in_event_loop = True
        while len(self.event_queue): # Renders may raise events!
            while len(self.event_queue):
                self.__dispatch_event_loop__(self.event_queue[0])
                self.event_queue.popleft()
            self.render()
        self._in_event_loop = False

    def __dispatch_event_loop__(self, event: Event):
        print(f"Got new event {event}")

        if isinstance(event, EngineEvent):
            for rider in self.event_riders:
                if isinstance(event, rider.event_type):
                    rider.roll_call(event)
                    return

            # Handle events addressed to the Haddocks

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
                f"Astrid did a roll call to brief about event {event} to the Riders, but nobody came. Please ask Hiccup to assign *someone* here. Oh, and she wants it done, fast!"
            )

        if not len(self.states):
            raise RenderingException(
                f"A Terrible Terror carrying a mail about {event} landed at house Haddock, but nobody was there! You should find Hiccup and make sure he's not captured again..."
            )


        print(f"Trying to mail event {event} to entities")
        for entity in self.entities.values():
            print(f"Trying to mail event {event} to entity: {entity}")
            for rider in self.entity_riders:
                if isinstance(entity, rider.entity_type):
                    rider.roll_call(entity, event)


        for rider in self.state_riders:
            if isinstance(self.states[-1], rider.state_type):
                rider.roll_call(self.states[-1], event)

                return

        raise RenderingException(
            f"Astrid did a roll call to brief about event {event} on state {self.states[-1]}, but nobody came. Please ask Hiccup to assign *someone* here. Oh, and she wants it done, fast!"
        )

    def mail_event(self, event: Event):
        print(f"Sending a Terrible Terror to tell {event}...")
        self.event_queue.append(event)
        self._dispatch_events()

    def enroll_rider(self, rider: StateRider | EntityRider | EventRider):
        if isinstance(rider, StateRider):
            self.state_riders.append(rider)
        if isinstance(rider, EntityRider):
            self.entity_riders.append(rider)
        if isinstance(rider, EventRider):
            self.event_riders.append(rider)

    def declare_chief(self, chief: RenderChief):
        self.render_chiefs.append(chief)

    def register_clan(self, clan):
        for rider in clan.riders:
            self.enroll_rider(rider)

        for chief in clan.chiefs:
            self.declare_chief(chief)

        print(
            f"Clan {clan.__name__} has officially moved to Berk! The entire village celebrates a new ally to defend all of our dragons."
        )

    def call_entity(self, position: EntityID, default: Callable[[], Entity] | None = None):
        if position in self.entities:
            return self.entities[position]
        elif default is not None:
            return self.entities.setdefault(position, default())
        else:
            raise KeyError(position)

    def call_entities(self, clan=None, species=None, name=None):
        entities = []
        for k, v in self.entities.items():
            if (
                (k.clan == clan or clan == None)
                and (k.species == species or species == None)
                and (k.name == name or name == None)
            ):
                entities.append((k,v))

        return entities


Riders: TypeAlias = list[EventRider | StateRider | EntityRider]
Chiefs: TypeAlias = list[RenderChief]

chieftain: Hiccup = None  # type: ignore

# IMPORTANT NOTE: The EntityID for the player (i.e. player data like health) is stored as EntityID("haddock", "player", "player")
