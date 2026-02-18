import ast
from dataclasses import dataclass
from typing import List, Tuple, Any, Dict
import haddock
import dragonic.base
import dragonic.core
import dragonic.interactions
import uuid
from clans.hofferson import finn, astrid
import librarians.core

class Player(haddock.Entity):
    name: str
    health: int = 100

    def __init__(self, name: str):
        self.name = name

# Raise to suspend the Dragonic script at any location
class InterceptedCallException(Exception):
    pass


class ReturnDataEvent(haddock.Event):
    data: Any
    script: str

    def __init__(self, data, script):
        self.data = data
        self.script = script


class SendPromptEvent(haddock.EngineEvent):
    options: list[str]
    script: str

    def __init__(self, options, script) -> None:
        self.options = options
        self.script = script


class SendPromptEventRider(haddock.EventRider[SendPromptEvent]):
    event_type = SendPromptEvent

    def roll_call(self, event: SendPromptEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(
                Prompt(
                    [
                        (
                            option,
                            haddock.EventSeries(
                                [
                                    ReturnDataEvent(
                                        dragonic.interactions.DialogueResult(i, option), event.script
                                    ),
                                    haddock.PopStateEvent(),
                                ]
                            ),
                        )
                        for i, option in enumerate(event.options)
                    ],
                    event.script,
                )
            )
        )


class Prompt(haddock.State):
    options: list[tuple[str, haddock.Event]]
    script: str

    def __init__(self, options=None, script=None):
        if options is None:
            options = []
        self.options = options
        self.script = script  # type: ignore


class PromptRenderCommand(haddock.RenderCommand):
    options: list[tuple[str, haddock.Event]]


class PromptRider(haddock.StateRider[Prompt]):
    state_type = Prompt

    def roll_call(self, state: Prompt, event: haddock.Event) -> None:
        pass

    def render(self, state: Prompt) -> haddock.RenderCommand:
        command = PromptRenderCommand()
        command.options = state.options
        return command


class PromptRenderChief(haddock.RenderChief[PromptRenderCommand]):
    command_type = PromptRenderCommand

    def render(self, command: PromptRenderCommand, application) -> None:
        application.send_prompt(command.options)


class SendDialogueEvent(haddock.EngineEvent):
    character: str
    line: str
    script: str

    def __init__(self, character, line, script) -> None:
        self.character = character
        self.line = line
        self.script = script


class SendDialogueEventRider(haddock.EventRider[SendDialogueEvent]):
    event_type = SendDialogueEvent

    def roll_call(self, event: SendDialogueEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(
                Dialogue(event.character, event.line, event.script)
            )
        )


class Dialogue(haddock.State):
    character: str
    line: str
    script: str

    def __init__(self, character, line, script):
        self.character = character
        self.line = line
        self.script = script


class DialogueRenderCommand(haddock.RenderCommand):
    character: str
    line: str
    script: str


class DialogueRider(haddock.StateRider[Dialogue]):
    state_type = Dialogue

    def roll_call(self, state: Dialogue, event: haddock.Event) -> None:
        pass

    def render(self, state: Dialogue) -> haddock.RenderCommand:
        command = DialogueRenderCommand()
        command.line = state.line
        command.character = state.character
        command.script = state.script
        return command


class DialogueRenderChief(haddock.RenderChief[DialogueRenderCommand]):
    command_type = DialogueRenderCommand

    def render(self, command: DialogueRenderCommand, application) -> None:
        application.send_dialogue(command.character, command.line)
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())


class SendStoryEvent(haddock.EngineEvent):
    line: str
    script: str

    def __init__(self, line, script) -> None:
        self.line = line
        self.script = script


class SendStoryEventRider(haddock.EventRider[SendStoryEvent]):
    event_type = SendStoryEvent

    def roll_call(self, event: SendStoryEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(Story(event.line, event.script))
        )


class Story(haddock.State):
    line: str
    script: str

    def __init__(self, line, script):
        self.line = line
        self.script = script


class StoryRenderCommand(haddock.RenderCommand):
    line: str
    script: str


class StoryRider(haddock.StateRider[Story]):
    state_type = Story

    def roll_call(self, state: Story, event: haddock.Event) -> None:
        pass

    def render(self, state: Story) -> haddock.RenderCommand:
        command = StoryRenderCommand()
        command.line = state.line
        command.script = state.script
        return command


class StoryRenderChief(haddock.RenderChief[StoryRenderCommand]):
    command_type = StoryRenderCommand

    def render(self, command: StoryRenderCommand, application) -> None:
        application.send_story(command.line)
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())


Block = Tuple[list[ast.stmt], int]


@dataclass
class DragonicState(haddock.State):
    block_stack: List[Block]
    globals: dict


class DragonicQuest(haddock.Entity):
    data_stream: List[dragonic.base.ValueLike]
    id: str

    def __init__(self, id: str, data_stream: List[dragonic.base.ValueLike] = []):
        source = librarians.core.get_data(["quest", id], "py", False)
        self.id = id
        self.data_stream = data_stream

        namespace = {}
        exec(source, namespace)
        self.coro = namespace["main"]()

        for data in self.data_stream:
            self.step(data, False)

    def step(self, data, dispatch_events=True):
        try:
            if dispatch_events:
                self.data_stream.append(data)
            syscall = self.coro.send(data)
            if dispatch_events:
                if isinstance(syscall, dragonic.interactions.AddCharacterHookSyscall):
                    character = syscall.character
                    line = syscall.line
                    line_id = str(uuid.uuid4())
                    event = haddock.EventSeries([astrid.RemoveDialogueEvent(character, line_id), ReturnDataEvent(None, self.id)])
                    haddock.chieftain.mail_event(astrid.AddDialogueEvent(character, line, event, line_id))
                    return

                if isinstance(syscall, dragonic.interactions.SendDialogueSyscall):
                    character = syscall.speaker
                    line = syscall.line
                    haddock.chieftain.mail_event(SendDialogueEvent(character, line, self.id))
                    return
        
                if isinstance(syscall, dragonic.interactions.SendPromptSyscall):
                    options = syscall.options
                    haddock.chieftain.mail_event(SendPromptEvent(options, self.id))
                    return

                if isinstance(syscall, dragonic.interactions.SendStorySyscall):
                    line = syscall.text
                    haddock.chieftain.mail_event(SendStoryEvent(line, self.id))
                    return

                if isinstance(syscall, dragonic.base.ReadAttrSyscall):
                    if syscall.path[0] == dragonic.base.Attr("player"):
                        if syscall.path[1] == dragonic.base.Attr("name"):
                            return self.step(haddock.chieftain.call_entity(haddock.EntityID("jorgenson", "player", "player")).name)
                        if syscall.path[1] == dragonic.base.Attr("health"):
                            return self.step(haddock.chieftain.call_entity(haddock.EntityID("jorgenson", "player", "player")).health)

                    print(f"Unrecognized path: {syscall.path}")

                raise RuntimeError(f"Unknown Syscall {syscall.__repr__()}")
        except StopIteration:
            pass


class DragonicQuestRider(haddock.EntityRider[DragonicQuest]):
    entity_type = DragonicQuest

    def roll_call(self, entity: DragonicQuest, event: haddock.Event) -> None:
        if isinstance(event, ReturnDataEvent) and event.script == entity.id:
            entity.step(event.data)

        if isinstance(event, haddock.TeamAssmebled) and not len(entity.data_stream):
            entity.step(None)


riders: haddock.Riders = [
    PromptRider(),
    DialogueRider(),
    StoryRider(),
    DragonicQuestRider(),
    SendPromptEventRider(),
    SendDialogueEventRider(),
    SendStoryEventRider(),
]

chiefs: haddock.Chiefs = [
    PromptRenderChief(),
    DialogueRenderChief(),
    StoryRenderChief(),
]
