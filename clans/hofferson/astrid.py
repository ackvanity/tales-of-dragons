import haddock
from librarians.hofferson import astrid
from librarians import core
from clans.hofferson import Action
import random

modules = []


class HumanInteractEventBase:
    to: str

    def __init__(self, to: str):
        self.to = to


class HumanInteractEngineEvent(HumanInteractEventBase, haddock.EngineEvent):
    pass


class HumanInteractEvent(HumanInteractEventBase, haddock.Event):
    pass


class HumanInteractRider(haddock.EventRider[HumanInteractEngineEvent]):
    event_type = HumanInteractEngineEvent

    def roll_call(self, event: HumanInteractEngineEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Talking(event.to)))

class AddDialogueEvent(haddock.EngineEvent):
    character: str
    line: str
    event: haddock.Event
    id: str

    def __init__(self, character, line, event, id):
        self.character = character
        self.line = line
        self.event = event
        self.id = id

class BaseAddDialogueEvent(haddock.Event):
    character: str
    line: str
    event: haddock.Event
    id: str

    def __init__(self, character, line, event, id):
        self.character = character
        self.line = line
        self.event = event
        self.id = id

class AddDialogueEventRider(haddock.EventRider[AddDialogueEvent]):
    event_type = AddDialogueEvent

    def roll_call(self, event: AddDialogueEvent) -> None:
        get_human(event.character)
        haddock.chieftain.mail_event(BaseAddDialogueEvent(event.character, event.line, event.event, event.id))

class RemoveDialogueEvent(haddock.Event):
    character: str
    id: str

    def __init__(self, character, id):
        self.character = character
        self.id = id


class Human(haddock.Entity):
    id: str
    name: str
    health: int = 100
    location: str

    extra_character_actions: list[Action]

    def __init__(self, id):
        self.id = id
        self.health = astrid.parse_character_data(
            core.get_data(f"character/human/{id}")
        ).variables.health
        self.location = astrid.parse_character_data(
            core.get_data(f"character/human/{id}")
        ).variables.location
        self.name = astrid.parse_character_data(
            core.get_data(f"character/human/{id}")
        ).name
        self.extra_character_actions = []

    @property
    def actions(self) -> list[Action]:
        return [Action(line=f"Goodbye {self.name}", signal=haddock.PopStateEvent())]

    @property
    def line(self) -> str:
        return random.choice(
            astrid.parse_character_data(
                core.get_data(f"character/human/{self.id}")
            ).menu_lines
        )


class Talking(haddock.State):
    to: str

    @property
    def version(self) -> int:
        return 1

    def __init__(self, to: str):
        self.to = to

    def _serialize(self) -> haddock.JSONValue:
        return self.to

    @classmethod
    def _deserialize(cls: type["Talking"], data: haddock.JSONValue, version: int) -> "Talking":
        if version == 1:
            if not isinstance(data, str):
                raise haddock.DeserializeException(f"Expected str for Talking.to, got {data!r}")
            return cls(data)
        else:
            raise haddock.DeserializeVersionUnsupportedException()


class TalkingRenderCommand(haddock.RenderCommand):
    speaker: str
    line: str
    actions: list[Action]

    def __init__(self, speaker: str, line: str, actions: list[Action]):
        self.speaker = speaker
        self.line = line
        self.actions = actions


class HumanRider(haddock.EntityRider[Human]):
    entity_type = Human

    def roll_call(self, entity: Human, event: haddock.Event) -> None:
        print(f"Got event {event}")
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
            entity.extra_character_actions = [a for a in entity.extra_character_actions if a.id != event.id]


class TalkingRider(haddock.StateRider[Talking]):
    state_type = Talking

    def roll_call(self, state: Talking, event: haddock.Event) -> None:
        if isinstance(event, HumanInteractEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())
            haddock.chieftain.mail_event(HumanInteractEngineEvent(event.to))

    def render(self, state: Talking) -> haddock.RenderCommand:
        character = get_human(state.to)

        actions: list[Action] = []
        actions += character.actions
        actions += character.extra_character_actions
        for module in modules:
            actions += module.extra_character_actions

        return TalkingRenderCommand(character.name, character.line, actions)


def get_human(name: str) -> Human:
    return haddock.chieftain.call_entity(haddock.EntityID("hofferson", "human", name), lambda: Human(name))  # type: ignore


riders: haddock.Riders = [HumanRider(), TalkingRider(), HumanInteractRider(), AddDialogueEventRider()]
chiefs: haddock.Chiefs = []
