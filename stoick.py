from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, Button
from textual.containers import VerticalScroll, VerticalGroup
from textual.reactive import reactive
import haddock
from clans.ingerman import fishlegs
import asyncio

from components.base import EventEmitButton
from components.ingerman.fishlegs import SatchelItems, SatchelList
from components.hofferson import Story
from components.hofferson.astrid import Character
from components.hofferson.finn import Location
from components.hofferson import Prompt, Dialogue, Paragraph


class TextualApplication(App):
  def compose(self) -> ComposeResult:
    yield Header()
    yield VerticalGroup(id="application")
    yield Footer()
  
  async def clear_history(self):
    group = self.query_one("#application")
    children = list(group.children)

    for child in children:
      await child.remove()
  
  async def ensure_singleton(self, klass: type):
    group = self.query_one("#application")
    children = list(group.children)

    if len(children) != 1 or type(children[0]) != klass:
      await self.clear_history()
      await self.query_one("#application").mount(klass())

  async def _send_to_story(self, widget):
    await self.ensure_singleton(Story)
    story = self.query_one("#application").children[0]
    widget.mount_self(story)

  def send_location(self, location):
    asyncio.create_task(self._send_to_story(Location(location)))

  def send_character(self, character):
    asyncio.create_task(self._send_to_story(Character(character)))
  
  def send_satchel_list(self, satchels):
      async def x(): 
        widget = SatchelList(satchels)
        await self.clear_history()
        await self.query_one("#application").mount(widget)

      asyncio.create_task(x())

  def send_satchel_items(self, items):
      async def x(): 
        widget = SatchelItems(items)
        await self.clear_history()
        await self.query_one("#application").mount(widget)

      asyncio.create_task(x())
  
  async def _append_to_story(self, node):
    await self.ensure_singleton(Story)
    story = self.query_one("#application").children[0]
    story.nodes.append(node) # type: ignore
    story.refresh(recompose=True)

  def send_prompt(self, options):
    prompt = Prompt()
    for option in options:
      prompt.options.append(EventEmitButton(option[0], option[1]))
    asyncio.create_task(self._append_to_story(prompt))

  def send_dialogue(self, character, line):
    asyncio.create_task(self._append_to_story(Dialogue(character, line)))

  def send_story(self, line):
    asyncio.create_task(self._append_to_story(Paragraph(line)))

  def on_mount(self) -> None:
    haddock.chieftain.mail_event(haddock.TeamAssembled())