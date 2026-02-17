from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import VerticalScroll
from textual.reactive import reactive
import haddock
from clans.ingerman import fishlegs
from components.base import EventEmitButton

class SatchelList(VerticalScroll):
  satchels: reactive[list[tuple[str, haddock.Event]]] = reactive([])

  def __init__(self, satchels = []):
    super().__init__()
    self.satchels = satchels
  
  def compose(self) -> ComposeResult:
    for satchel in self.satchels:
      yield EventEmitButton(satchel[0], satchel[1])
    yield EventEmitButton("Go Back.", fishlegs.CloseSatchelsListEvent())

class SatchelItems(VerticalScroll):
  items: reactive[list[fishlegs.Item]] = reactive([])
  title: reactive[str] = reactive("")

  def __init__(self, items={"items": [], "title": ""}):
    super().__init__()
    
    self.items = items["items"]
    self.title = items["title"]
  
  def compose(self) -> ComposeResult:
    yield Label(self.title)
    for item in self.items:
      yield Label(item.name)
      yield Label(item.description)
    yield EventEmitButton("Go Back.", fishlegs.CloseSatchelItemsEvent())