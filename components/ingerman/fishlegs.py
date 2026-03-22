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
  satchels: reactive[list[tuple[str, haddock.Event]]] = reactive([])

  def __init__(self, satchels: list[tuple[str, haddock.Event]] = []):
    super().__init__()
    self.satchels = satchels

  def compose(self) -> ComposeResult:
    for name, event in self.satchels:
      yield EventEmitButton(name, event)
    yield EventEmitButton("Go Back.", CloseSatchelsListEvent())


class SatchelItems(VerticalScroll):
  items: reactive[list[BaseItem]] = reactive([])
  title: reactive[str] = reactive("")

  def __init__(self, title: str = "", items: list[BaseItem] = []):
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
  command_type = SatchelsListRenderCommand

  def render(self, command: SatchelsListRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.clear_history()
      await application.get_mount_point().mount(SatchelList(command.satchels))

    asyncio.create_task(_render())


class SatchelItemsRenderChief(haddock.RenderChief[SatchelItemsRenderCommand]):
  command_type = SatchelItemsRenderCommand

  def render(self, command: SatchelItemsRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.clear_history()
      await application.get_mount_point().mount(SatchelItems(command.title, command.items))

    asyncio.create_task(_render())
