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

  def send_location(self, location):
    widget = Location(location)
    group = self.query_one("#application")
    asyncio.create_task(self.ensure_singleton(Story)).add_done_callback(lambda _: widget.mount_self(group.children[0])) # type: ignore

  def send_character(self, character):
    widget = Character(character)
    group = self.query_one("#application")
    asyncio.create_task(self.ensure_singleton(Story)).add_done_callback(lambda _: widget.mount_self(group.children[0])) # type: ignore
  
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
  
  def send_prompt(self, options):
    group = self.query_one("#application")

    def x(_):
      story = group.children[0]
      prompt = Prompt()
      story.nodes.append(prompt) # type: ignore
      for option in options:
        prompt.options.append(EventEmitButton(option[0], option[1]))
      
      print(f"Added option: {prompt.options}")
      print(f"{story.nodes}") # type: ignore
      story.refresh(recompose=True)
      
    asyncio.create_task(self.ensure_singleton(Story)).add_done_callback(x)

  def send_dialogue(self, character, line):
    group = self.query_one("#application")

    def x(_):
      story = group.children[0]
      dialogue = Dialogue(character, line)
      story.nodes.append(dialogue) # type: ignore
      story.refresh(recompose=True)
      
    asyncio.create_task(self.ensure_singleton(Story)).add_done_callback(x)
    
  def send_story(self, line):
    print("SENDING STORY", line)
    group = self.query_one("#application")

    def x(_):
      story = group.children[0]
      dialogue = Paragraph(line)
      story.nodes.append(dialogue) # type: ignore
      story.refresh(recompose=True)
      
    asyncio.create_task(self.ensure_singleton(Story)).add_done_callback(x)

  def on_mount(self) -> None:
    haddock.chieftain.mail_event(haddock.TeamAssmebled())