import haddock
from librarians.hofferson import astrid
from librarians import core
import copy
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

class DialogueAction:
    @property
    def line(self) -> str: ...

    condition: str
    signal: haddock.Event
    id: str


class LiteralDialogueAction(DialogueAction):
    _line: str

    @property
    def line(self) -> str:
        return self._line

    @line.setter
    def line(self, line: str) -> None:
        self._line = line

    condition: str = "True"


class Human(haddock.Entity):
    id: str
    name: str
    health: int = 100
    location: str

    extra_lines: list[DialogueAction]

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
        self.extra_lines = []

    @property
    def actions(self) -> list[LiteralDialogueAction]:
        goodbye = LiteralDialogueAction()
        goodbye.signal = haddock.PopStateEvent()
        goodbye.line = f"Goodbye {self.name}"
        return [goodbye]

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

    def _serialize(self) -> str:
        return self.to
    
    @classmethod
    def _deserialize(cls: type["Talking"], data: str, version: int) -> "Talking":
        if version == 1:
            return cls(data)
        else:
            raise haddock.DeserializeVersionUnsupportedException()


class TalkingRenderCommand(haddock.RenderCommand):
    speaker: str
    line: str
    actions: list[LiteralDialogueAction]

    def __init__(self, speaker: str, line: str, actions: list[LiteralDialogueAction]):
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
            print(f"Adding line!")
            action = LiteralDialogueAction()
            action.line = event.line
            action.signal = event.event
            action.id = event.id
            entity.extra_lines.append(action)
        if isinstance(event, RemoveDialogueEvent) and event.character == entity.id:
            entity.extra_lines = [line for line in entity.extra_lines if line.id != event.id]


class TalkingRider(haddock.StateRider[Talking]):
    state_type = Talking

    def roll_call(self, state: Talking, event: haddock.Event) -> None:
        if isinstance(event, HumanInteractEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())
            haddock.chieftain.mail_event(HumanInteractEngineEvent(event.to))

    def render(self, state: Talking) -> haddock.RenderCommand:
        character = get_human(state.to)

        actions = copy.deepcopy(character.actions)
        actions += character.extra_lines 
        for module in modules:
            for action in module.extra_character_actions:
                actions.append(action)

        return TalkingRenderCommand(character.name, character.line, actions) # type: ignore


class TalkingRenderChief(haddock.RenderChief[TalkingRenderCommand]):
    command_type = TalkingRenderCommand

    def render(self, command: TalkingRenderCommand, application) -> None:
        render_state = {
            "speaker": command.speaker,
            "line": command.line,
            "actions": [
                {"line": action.line, "signal": action.signal}
                for action in command.actions
            ],
        }

        application.send_character(render_state)


def get_human(name: str) -> Human:
    return haddock.chieftain.call_entity(haddock.EntityID("hofferson", "human", name), lambda: Human(name))  # type: ignore


riders: haddock.Riders = [HumanRider(), TalkingRider(), HumanInteractRider(), AddDialogueEventRider()]
chiefs: haddock.Chiefs = [TalkingRenderChief()]
