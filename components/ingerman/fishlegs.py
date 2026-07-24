"""
components/ingerman/fishlegs.py — Inventory View components.

Contains Textual widgets and RenderChiefs for the inventory system:
  - SatchelList:            scrollable list of satchels to open.
  - SatchelItems:           scrollable view of a satchel's contents.
  - SatchelsListRenderChief: renders the SatchelsList state.
  - SatchelItemsRenderChief: renders the SatchelItems state.
"""

import asyncio
import haddock
from clans.ingerman.fishlegs import (
    SatchelsListRenderCommand,
    SatchelItemsRenderCommand,
    CloseSatchelsListEvent,
    CloseSatchelItemsEvent,
    BaseItem,
)
from stoick import TextualApplication


class SatchelsListRenderChief(haddock.RenderChief[SatchelsListRenderCommand]):
    """
    Renders the SatchelsList state by mounting a SatchelList widget.

    Clears the current view and replaces it with the satchel list.
    All DOM work runs in an asyncio task.
    """

    command_type = SatchelsListRenderCommand

    def render(
        self,
        command: SatchelsListRenderCommand,
        application: TextualApplication,
    ) -> None:
                SatchelList(command.satchels)


class SatchelItemsRenderChief(haddock.RenderChief[SatchelItemsRenderCommand]):
    """
    Renders the SatchelItems state by mounting a SatchelItems widget.

    Clears the current view and replaces it with the satchel contents.
    All DOM work runs in an asyncio task.
    """

    command_type = SatchelItemsRenderCommand

    def render(
        self,
        command: SatchelItemsRenderCommand,
        application: TextualApplication,
    ) -> None:
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(
                SatchelItems(command.title, command.items)
            )

        asyncio.create_task(_render())
