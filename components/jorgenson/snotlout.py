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
from components.base import EventEmitButton
from components.hofferson import Story, Prompt, Dialogue, Paragraph
from stoick import TextualApplication


class PromptRenderChief(haddock.RenderChief[PromptRenderCommand]):
    """
    Renders the Prompt state by appending a Prompt widget to the Story.

    Each option in the command is rendered as an EventEmitButton.
    The quest coroutine is already suspended at this point and will
    resume when the player selects an option (via ReturnDataEvent).
    """

    command_type = PromptRenderCommand

    def render(self, command: PromptRenderCommand, application: TextualApplication) -> None:
        async def _render() -> None:
            await application.ensure_singleton(Story)
            story = application.get_story()
            if story is not None:
                prompt = Prompt()
                for label, event in command.options:
                    prompt.options.append(EventEmitButton(label, event))
                story.nodes.append(prompt)
                story.refresh(recompose=True)

        asyncio.create_task(_render())


class DialogueRenderChief(haddock.RenderChief[DialogueRenderCommand]):
    """
    Renders the Dialogue state by appending a Dialogue widget to the Story.

    Auto-advances: fires ReturnDataEvent(None) to resume the quest coroutine
    and pops the Dialogue state immediately after scheduling the widget mount.
    The player sees the line but does not need to dismiss it.
    """

    command_type = DialogueRenderCommand

    def render(self, command: DialogueRenderCommand, application: TextualApplication) -> None:
        async def _render() -> None:
            await application.ensure_singleton(Story)
            story = application.get_story()
            if story is not None:
                story.nodes.append(Dialogue(command.character, command.line))
                story.refresh(recompose=True)

        asyncio.create_task(_render())
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())


class StoryRenderChief(haddock.RenderChief[StoryRenderCommand]):
    """
    Renders the Story state by appending a Paragraph widget to the Story.

    Auto-advances: fires ReturnDataEvent(None) and pops state immediately,
    same as DialogueRenderChief.
    """

    command_type = StoryRenderCommand

    def render(self, command: StoryRenderCommand, application: TextualApplication) -> None:
        async def _render() -> None:
            await application.ensure_singleton(Story)
            story = application.get_story()
            if story is not None:
                story.nodes.append(Paragraph(command.line))
                story.refresh(recompose=True)

        asyncio.create_task(_render())
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())
