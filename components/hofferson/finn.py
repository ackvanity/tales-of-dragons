"""
components/hofferson/finn.py — Location navigation View components.

Contains the Location presentation helper and WanderingRenderChief, which
renders the Wandering state (location exploration screen) into Textual widgets.
"""

import asyncio
import haddock
from clans.hofferson.finn import WanderingRenderCommand
from components.base import EventEmitButton
from . import Paragraph, Prompt, Story
from stoick import TextualApplication


class Location:
    """
    Presentation helper that mounts a location scene into a Story widget.

    Unpacks a WanderingRenderCommand and appends a Paragraph node (ambient
    description) and a Prompt node (all available navigation/interaction
    actions) to the Story.

    Attributes:
        location_id:      Current location identifier.
        location_ambient: Scene-setting description shown to the player.
        location_actions: List of selectable navigation and interaction options.
    """

    def __init__(self, command: WanderingRenderCommand) -> None:
        self.location_id = command.id
        self.location_ambient = command.ambient
        self.location_actions = command.actions

    def mount_self(self, story: Story) -> None:
        """Append ambient description and action prompt to the story, then recompose."""
        prompt = Prompt()
        story.nodes.append(Paragraph(self.location_ambient))
        story.nodes.append(prompt)
        story.refresh(recompose=True)
        for action in self.location_actions:
            prompt.options.append(EventEmitButton(action.line, action.signal))


class WanderingRenderChief(haddock.RenderChief[WanderingRenderCommand]):
    """
    Renders the Wandering state by mounting a Location scene into the Story.

    Ensures the Story singleton exists before mounting, then delegates
    to Location.mount_self(). All DOM work runs in an asyncio task.
    """

    command_type = WanderingRenderCommand

    def render(self, command: WanderingRenderCommand, application: TextualApplication) -> None:
        async def _render() -> None:
            await application.ensure_singleton(Story)
            story = application.get_story()
            if story is not None:
                Location(command).mount_self(story)

        asyncio.create_task(_render())
