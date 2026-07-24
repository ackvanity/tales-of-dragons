"""
components/jorgenson/snotlout.py — Dragonic narrative View components.

Contains RenderChiefs for the three Dragonic output states:
  - PromptRenderChief:    renders player choice menus.
  - DialogueRenderChief:  renders character dialogue lines (auto-advance).
  - StoryRenderChief:     renders narration paragraphs (auto-advance).

Auto-advance chiefs fire ReturnDataEvent immediately after mounting widgets
and pop their state, so the Dragonic quest coroutine resumes without
requiring any player action.
"""

import asyncio
import haddock
from clans.jorgenson.snotlout import (
    PromptRenderCommand,
    DialogueRenderCommand,
    StoryRenderCommand,
    ReturnDataEvent,
)

class PromptRenderChief(haddock.RenderChief[PromptRenderCommand]):
    """
    Renders the Prompt state by appending a Prompt widget to the Story.

    Each option in the command is rendered as an EventEmitButton.
    The quest coroutine is already suspended at this point and will
    resume when the player selects an option (via ReturnDataEvent).
    """

    command_type = PromptRenderCommand

    def render(
        self, command: PromptRenderCommand, application
    ) -> None:
        # data = []
        # for label, event in command.options:
        #     data.append([label, haddock.serialize(event)])

        application.send_data("prompt", [[label, haddock.serialize(event)] for label, event in command.options])


class DialogueRenderChief(haddock.RenderChief[DialogueRenderCommand]):
    """
    Renders the Dialogue state by appending a Dialogue widget to the Story.

    Auto-advances: fires ReturnDataEvent(None) to resume the quest coroutine
    and pops the Dialogue state immediately after scheduling the widget mount.
    The player sees the line but does not need to dismiss it.
    """

    command_type = DialogueRenderCommand

    def render(
        self, command: DialogueRenderCommand, application
    ) -> None:
        application.send_data("dialogue", [command.character, command.line])

        haddock.chieftain.mail_event(haddock.EventSeries([haddock.PopStateEvent(),ReturnDataEvent(None, command.script)]))


class StoryRenderChief(haddock.RenderChief[StoryRenderCommand]):
    """
    Renders the Story state by appending a Paragraph widget to the Story.

    Auto-advances: fires ReturnDataEvent(None) and pops state immediately,
    same as DialogueRenderChief.
    """

    command_type = StoryRenderCommand

    def render(
        self, command: StoryRenderCommand, application
    ) -> None:
        application.send_data("story", command.line)

        haddock.chieftain.mail_event(haddock.EventSeries([haddock.PopStateEvent(),ReturnDataEvent(None, command.script)]))
