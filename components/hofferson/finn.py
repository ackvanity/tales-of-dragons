"""
components/hofferson/finn.py — Location navigation View components.

Contains the Location presentation helper and WanderingRenderChief, which
renders the Wandering state (location exploration screen) into Textual widgets.
"""

import json
import haddock
from clans.hofferson.finn import WanderingRenderCommand

class WanderingRenderChief(haddock.RenderChief[WanderingRenderCommand]):
    """
    Renders the Wandering state by mounting a Location scene into the Story.

    Ensures the Story singleton exists before mounting, then delegates
    to Location.mount_self(). All DOM work runs in an asyncio task.
    """

    command_type = WanderingRenderCommand

    def render(
        self, command: WanderingRenderCommand, application
    ) -> None:
        application.send_data("story", command.ambient)
        application.send_data("prompt",[[action.line, haddock.serialize(action.signal)] for action in command.actions])
