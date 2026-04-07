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
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import VerticalScroll
from textual.reactive import reactive
from components.base import EventEmitButton
from stoick import TextualApplication


class SatchelList(VerticalScroll):
    """
    A scrollable list of satchels the player can open.

    Each satchel is rendered as an EventEmitButton that opens its contents.
    A "Go Back" button at the bottom dismisses the list.

    Attributes:
        satchels: List of (display name, open event) pairs.
    """

    satchels: reactive[list[tuple[str, haddock.Event]]] = reactive([])

    def __init__(self, satchels: list[tuple[str, haddock.Event]] = []) -> None:
        super().__init__()
        self.satchels = satchels

    def compose(self) -> ComposeResult:
        for name, event in self.satchels:
            yield EventEmitButton(name, event)
        yield EventEmitButton("Go Back.", CloseSatchelsListEvent())


class SatchelItems(VerticalScroll):
    """
    A scrollable view of a single satchel's contents.

    Items are displayed as name + description label pairs. Empty slots are
    shown as "Empty Slot" entries. A "Go Back" button dismisses the view.

    Attributes:
        title: Display title shown at the top (e.g. "Satchel (10 items)").
        items: All items including NoItem padding up to capacity.
    """

    items: reactive[list[BaseItem]] = reactive([])
    title: reactive[str] = reactive("")

    def __init__(self, title: str = "", items: list[BaseItem] = []) -> None:
        super().__init__()
        self.title = title
        self.items = items

    def compose(self) -> ComposeResult:
        yield Label(self.title)
        for item in self.items:
            yield Label(item.name)
            yield Label(item.description)
        yield EventEmitButton("Go Back.", CloseSatchelItemsEvent())


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
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(
                SatchelList(command.satchels)
            )

        asyncio.create_task(_render())


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
