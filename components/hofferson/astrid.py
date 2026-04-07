"""
components/hofferson/astrid.py — Character dialogue View components.

Contains the Character presentation helper and TalkingRenderChief, which
renders the Talking state (NPC dialogue screen) into Textual widgets.
"""

import asyncio
import haddock
from clans.hofferson.astrid import TalkingRenderCommand
from components.base import EventEmitButton
from . import Dialogue, Story, Prompt
from stoick import TextualApplication


class Character:
    """
    Presentation helper that mounts an NPC dialogue scene into a Story widget.

    Unpacks a TalkingRenderCommand and appends a Dialogue node (speaker +
    greeting line) and a Prompt node (all available actions) to the Story.

    Attributes:
        speaker:  NPC display name.
        line:     Greeting line shown above the action buttons.
        actions:  List of selectable actions (static + injected + module).
    """

    def __init__(self, command: TalkingRenderCommand) -> None:
        self.speaker = command.speaker
        self.line = command.line
        self.actions = command.actions

    def mount_self(self, story: Story) -> None:
        """Append dialogue and action prompt to the story, then recompose."""
        prompt = Prompt()
        story.nodes.append(Dialogue(self.speaker, self.line))
        story.nodes.append(prompt)
        story.refresh(recompose=True)
        for action in self.actions:
            prompt.options.append(EventEmitButton(action.line, action.signal))


class TalkingRenderChief(haddock.RenderChief[TalkingRenderCommand]):
    """
    Renders the Talking state by mounting a Character scene into the Story.

    Ensures the Story singleton exists before mounting, then delegates
    to Character.mount_self(). All DOM work runs in an asyncio task to
    avoid blocking the synchronous render pipeline.
    """

    command_type = TalkingRenderCommand

    def render(
        self, command: TalkingRenderCommand, application: TextualApplication
    ) -> None:
        async def _render() -> None:
            await application.ensure_singleton(Story)
            story = application.get_story()
            if story is not None:
                Character(command).mount_self(story)

        asyncio.create_task(_render())
