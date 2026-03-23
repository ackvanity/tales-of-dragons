"""
clans/jorgenson/snotlout.py — Player entity and Dragonic quest runtime.

Contains:
  - Player: the entity holding the player's name and health.
  - DragonicQuest: runs a quest coroutine and dispatches its syscalls.
  - Prompt / Dialogue / Story: transient states used by Dragonic to
    display content and collect player choices.
  - All associated events, riders, and render commands.

The Dragonic system works via Python coroutines and a syscall protocol:
quest scripts yield Syscall objects that the runtime intercepts, fires as
engine events, and resumes with the result once the player responds.
"""

import ast
from dataclasses import dataclass
from typing import List, Tuple
import haddock
import dragonic.base
import dragonic.core
import dragonic.interactions
import uuid
from clans.hofferson import astrid
import librarians.core


# ---------------------------------------------------------------------------
# Player entity
# ---------------------------------------------------------------------------

class Player(haddock.Entity):
    """
    The player character entity.

    Stored as EntityID("jorgenson", "player", "player").
    Readable from quest scripts via world.player.name and world.player.health.

    Attributes:
        name:   Player's display name (set at game start).
        health: Current health (default 100).
    """

    name: str
    health: int

    def __init__(self, name: str) -> None:
        self.name = name
        self.health = 100

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return {"name": self.name, "health": self.health}

    @classmethod
    def _deserialize(cls: type["Player"], data: haddock.JSONValue, version: int) -> "Player":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict for Player, got {data!r}")
            obj = cls(data["name"])  # type: ignore
            obj.health = data["health"]  # type: ignore
            return obj
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "jorgenson.Player"


# ---------------------------------------------------------------------------
# Internal exception (unused externally)
# ---------------------------------------------------------------------------

class InterceptedCallException(Exception):
    """Reserved for suspending a Dragonic script at an arbitrary point."""


# ---------------------------------------------------------------------------
# Dragonic return-data event
# ---------------------------------------------------------------------------

class ReturnDataEvent(haddock.Event):
    """
    Carries a return value back into a DragonicQuest coroutine.

    Fired after a player interaction (prompt selection, dialogue dismiss,
    story dismiss) to resume the quest coroutine with the result.

    Attributes:
        data:   The value to send into the coroutine (e.g. DialogueResult or None).
        script: The quest ID this return belongs to.
    """

    data: haddock.JSONValue
    script: str

    def __init__(self, data: haddock.JSONValue, script: str) -> None:
        self.data = data
        self.script = script


# ---------------------------------------------------------------------------
# Prompt state
# ---------------------------------------------------------------------------

class SendPromptEvent(haddock.EngineEvent):
    """Emitted by DragonicQuest to show the player a choice menu."""

    options: list[str]
    script: str

    def __init__(self, options: list[str], script: str) -> None:
        self.options = options
        self.script = script


class SendPromptEventRider(haddock.EventRider[SendPromptEvent]):
    """
    Pushes a Prompt state populated with options.

    Each option fires an EventSeries that sends a ReturnDataEvent with the
    DialogueResult back to the quest, then pops the Prompt state.
    """

    event_type = SendPromptEvent

    def roll_call(self, event: SendPromptEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(
                Prompt(
                    [
                        (
                            option,
                            haddock.EventSeries([
                                ReturnDataEvent(
                                    dragonic.interactions.DialogueResult(i, option),
                                    event.script,
                                ),
                                haddock.PopStateEvent(),
                            ]),
                        )
                        for i, option in enumerate(event.options)
                    ],
                    event.script,
                )
            )
        )


class Prompt(haddock.State):
    """
    Transient state showing a list of player choices.

    Populated by SendPromptEventRider and dismissed automatically when
    the player selects an option.

    Attributes:
        options: List of (label, signal event) pairs.
        script:  Quest ID waiting for the player's selection.
    """

    options: list[tuple[str, haddock.Event]]
    script: str

    def __init__(
        self,
        options: list[tuple[str, haddock.Event]] | None = None,
        script: str | None = None,
    ) -> None:
        self.options = options if options is not None else []
        self.script = script  # type: ignore

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        """Persist script only. Options contain Event objects and are reconstructed
        by the quest coroutine on replay."""
        return self.script

    @classmethod
    def _deserialize(cls: type["Prompt"], data: haddock.JSONValue, version: int) -> "Prompt":
        if version == 1:
            if not isinstance(data, str):
                raise haddock.DeserializeException(f"Expected str for Prompt.script, got {data!r}")
            return cls(options=None, script=data)
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "jorgenson.Prompt"


class PromptRenderCommand(haddock.RenderCommand):
    """Payload for rendering a player choice menu."""

    options: list[tuple[str, haddock.Event]]


class PromptRider(haddock.StateRider[Prompt]):
    """Renders the Prompt state. No event handling needed."""

    state_type = Prompt

    def roll_call(self, state: Prompt, event: haddock.Event) -> None:
        pass

    def render(self, state: Prompt) -> haddock.RenderCommand:
        command = PromptRenderCommand()
        command.options = state.options
        return command


# ---------------------------------------------------------------------------
# Dialogue state
# ---------------------------------------------------------------------------

class SendDialogueEvent(haddock.EngineEvent):
    """Emitted by DragonicQuest to show a character dialogue line."""

    character: str
    line: str
    script: str

    def __init__(self, character: str, line: str, script: str) -> None:
        self.character = character
        self.line = line
        self.script = script


class SendDialogueEventRider(haddock.EventRider[SendDialogueEvent]):
    """Pushes a Dialogue state for the given character line."""

    event_type = SendDialogueEvent

    def roll_call(self, event: SendDialogueEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(Dialogue(event.character, event.line, event.script))
        )


class Dialogue(haddock.State):
    """
    Transient state displaying a single character line.

    Auto-advances: DialogueRenderChief fires ReturnDataEvent(None) and pops
    this state immediately after mounting the widget.

    Attributes:
        character: Speaker's display name.
        line:      The line of dialogue to display.
        script:    Quest ID to resume after this line is shown.
    """

    character: str
    line: str
    script: str

    def __init__(self, character: str, line: str, script: str) -> None:
        self.character = character
        self.line = line
        self.script = script

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return {"character": self.character, "line": self.line, "script": self.script}

    @classmethod
    def _deserialize(cls: type["Dialogue"], data: haddock.JSONValue, version: int) -> "Dialogue":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict for Dialogue, got {data!r}")
            return cls(data["character"], data["line"], data["script"])  # type: ignore
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "jorgenson.Dialogue"


class DialogueRenderCommand(haddock.RenderCommand):
    """Payload for rendering a dialogue line."""

    character: str
    line: str
    script: str


class DialogueRider(haddock.StateRider[Dialogue]):
    """Renders the Dialogue state. No event handling needed (auto-advance)."""

    state_type = Dialogue

    def roll_call(self, state: Dialogue, event: haddock.Event) -> None:
        pass

    def render(self, state: Dialogue) -> haddock.RenderCommand:
        command = DialogueRenderCommand()
        command.line = state.line
        command.character = state.character
        command.script = state.script
        return command


# ---------------------------------------------------------------------------
# Story state
# ---------------------------------------------------------------------------

class SendStoryEvent(haddock.EngineEvent):
    """Emitted by DragonicQuest to show a narration paragraph."""

    line: str
    script: str

    def __init__(self, line: str, script: str) -> None:
        self.line = line
        self.script = script


class SendStoryEventRider(haddock.EventRider[SendStoryEvent]):
    """Pushes a Story state for the given narration text."""

    event_type = SendStoryEvent

    def roll_call(self, event: SendStoryEvent) -> None:
        haddock.chieftain.mail_event(
            haddock.AppendStateEvent(Story(event.line, event.script))
        )


class Story(haddock.State):
    """
    Transient state displaying a narration paragraph.

    Auto-advances like Dialogue: StoryRenderChief fires ReturnDataEvent(None)
    and pops immediately after mounting.

    Attributes:
        line:   The narration text to display.
        script: Quest ID to resume after this text is shown.
    """

    line: str
    script: str

    def __init__(self, line: str, script: str) -> None:
        self.line = line
        self.script = script

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return {"line": self.line, "script": self.script}

    @classmethod
    def _deserialize(cls: type["Story"], data: haddock.JSONValue, version: int) -> "Story":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict for Story, got {data!r}")
            return cls(data["line"], data["script"])  # type: ignore
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "jorgenson.Story"


class StoryRenderCommand(haddock.RenderCommand):
    """Payload for rendering a narration paragraph."""

    line: str
    script: str


class StoryRider(haddock.StateRider[Story]):
    """Renders the Story state. No event handling needed (auto-advance)."""

    state_type = Story

    def roll_call(self, state: Story, event: haddock.Event) -> None:
        pass

    def render(self, state: Story) -> haddock.RenderCommand:
        command = StoryRenderCommand()
        command.line = state.line
        command.script = state.script
        return command


# ---------------------------------------------------------------------------
# Dragonic quest runtime
# ---------------------------------------------------------------------------

Block = Tuple[list[ast.stmt], int]


@dataclass
class DragonicState(haddock.State):
    """
    Serializable snapshot of a Dragonic execution context.

    Not yet used — reserved for a future checkpoint-based save system
    as an alternative to full data_stream replay.
    """

    block_stack: List[Block]
    globals: dict

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        raise NotImplementedError("DragonicState serialization is not yet implemented")

    @classmethod
    def _deserialize(cls: type["DragonicState"], data: haddock.JSONValue, version: int) -> "DragonicState":
        raise NotImplementedError("DragonicState deserialization is not yet implemented")

    @staticmethod
    def tag() -> str:
        return "jorgenson.DragonicState"


class DragonicQuest(haddock.Entity):
    """
    Wraps and drives a running Dragonic quest coroutine.

    Stored as EntityID("jorgenson", "quest", <id>).

    The quest script (data/quest/<id>.py) is exec()'d at construction
    and its main() coroutine is started immediately. On game boot,
    TeamAssembled triggers the first step.

    Replay model:
        Every value sent into the coroutine is recorded in data_stream.
        On load, the coroutine is reconstructed and replayed from the start
        by feeding it the recorded stream. Quest scripts MUST be deterministic.

    Attributes:
        id:          Quest identifier matching the script filename.
        data_stream: All values ever sent into the coroutine (for replay).
        coro:        The live coroutine instance.
    """

    data_stream: List[dragonic.base.ValueLike]
    id: str

    def __init__(
        self,
        id: str,
        data_stream: List[dragonic.base.ValueLike] | None = None,
    ) -> None:
        source = librarians.core.get_data(["quest", id], "py", False)  # type: ignore
        self.id = id
        self.data_stream = data_stream if data_stream is not None else []

        namespace: dict = {}
        exec(source, namespace)  # type: ignore
        self.coro = namespace["main"]()

        for data in self.data_stream:
            self.step(data, dispatch_events=False)

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        """Persist the quest id only. data_stream contains DialogueResult objects
        which are not yet JSON-serializable; full replay serialization is deferred."""
        return self.id

    @classmethod
    def _deserialize(cls: type["DragonicQuest"], data: haddock.JSONValue, version: int) -> "DragonicQuest":
        if version == 1:
            if not isinstance(data, str):
                raise haddock.DeserializeException(f"Expected str for DragonicQuest.id, got {data!r}")
            return cls(data)  # type: ignore
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "jorgenson.DragonicQuest"

    def step(self, data: dragonic.base.ValueLike, dispatch_events: bool = True) -> None:
        """
        Advance the quest coroutine one step by sending data into it.

        Records data in data_stream (when dispatch_events=True) and handles
        the syscall the coroutine yields:
          - AddCharacterHookSyscall → inject a dialogue option into an NPC
          - SendDialogueSyscall     → show a dialogue line
          - SendPromptSyscall       → show a player choice menu
          - SendStorySyscall        → show a narration paragraph
          - ReadAttrSyscall         → read a game world attribute

        When dispatch_events=False (replay mode), syscalls are consumed
        without firing engine events.
        """
        try:
            if dispatch_events:
                self.data_stream.append(data)
            syscall = self.coro.send(data)

            if not dispatch_events:
                return

            if isinstance(syscall, dragonic.interactions.AddCharacterHookSyscall):
                character = syscall.character
                line = syscall.line
                line_id = str(uuid.uuid4())
                event = haddock.EventSeries([
                    astrid.RemoveDialogueEvent(character, line_id),
                    ReturnDataEvent(None, self.id),
                ])
                haddock.chieftain.mail_event(
                    astrid.AddDialogueEvent(character, line, event, line_id)
                )
                return

            if isinstance(syscall, dragonic.interactions.SendDialogueSyscall):
                haddock.chieftain.mail_event(
                    SendDialogueEvent(syscall.speaker, syscall.line, self.id)
                )
                return

            if isinstance(syscall, dragonic.interactions.SendPromptSyscall):
                haddock.chieftain.mail_event(SendPromptEvent(syscall.options, self.id))
                return

            if isinstance(syscall, dragonic.interactions.SendStorySyscall):
                haddock.chieftain.mail_event(SendStoryEvent(syscall.text, self.id))
                return

            if isinstance(syscall, dragonic.base.ReadAttrSyscall):
                if syscall.path[0] == dragonic.base.Attr("player"):
                    player = haddock.chieftain.call_entity(
                        haddock.EntityID("jorgenson", "player", "player")
                    )  # type: ignore
                    if syscall.path[1] == dragonic.base.Attr("name"):
                        return self.step(player.name)  # type: ignore
                    if syscall.path[1] == dragonic.base.Attr("health"):
                        return self.step(player.health)  # type: ignore
                print(f"Unrecognized path: {syscall.path}")

            raise RuntimeError(f"Unknown Syscall {syscall.__repr__()}")

        except StopIteration:
            pass


class DragonicQuestRider(haddock.EntityRider[DragonicQuest]):
    """
    Drives DragonicQuest entities by feeding them return data.

    Listens for:
      - ReturnDataEvent addressed to this quest → resume the coroutine
      - TeamAssembled (first boot, empty data_stream) → start the quest
    """

    entity_type = DragonicQuest

    def roll_call(self, entity: DragonicQuest, event: haddock.Event) -> None:
        if isinstance(event, ReturnDataEvent) and event.script == entity.id:
            entity.step(event.data)
        if isinstance(event, haddock.TeamAssembled) and not len(entity.data_stream):
            entity.step(None)


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

riders: haddock.Riders = [
    PromptRider(),
    DialogueRider(),
    StoryRider(),
    DragonicQuestRider(),
    SendPromptEventRider(),
    SendDialogueEventRider(),
    SendStoryEventRider(),
]

chiefs: haddock.Chiefs = []
