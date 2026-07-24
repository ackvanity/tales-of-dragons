"""
components/hofferson/astrid.py — Character dialogue View components.

Contains the Character presentation helper and TalkingRenderChief, which
renders the Talking state (NPC dialogue screen) into Textual widgets.
"""

import json
import haddock
from clans.hofferson.astrid import TalkingRenderCommand

class TalkingRenderChief(haddock.RenderChief[TalkingRenderCommand]):
    """
    Renders the Talking state by mounting a Character scene into the Story.

    Ensures the Story singleton exists before mounting, then delegates
    to Character.mount_self(). All DOM work runs in an asyncio task to
    avoid blocking the synchronous render pipeline.
    """

    command_type = TalkingRenderCommand

    def render(
        self, command: TalkingRenderCommand, application
    ) -> None:
        application.send_data("dialogue", command.speaker, command.line)
        application.send_data("prompt", [[action.line, haddock.serialize(action.signal)] for action in command.actions])

