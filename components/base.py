from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, Button
from textual.containers import VerticalScroll, VerticalGroup
from textual.reactive import reactive
import haddock
from clans.ingerman import fishlegs

class EventEmitButton(Button):
  event: reactive[haddock.Event] = reactive(haddock.Event())

  def __init__(self, line="", haddock_event=haddock.Event()):
    super().__init__(line)
    self.event = haddock_event

  def on_button_pressed(self, event: Button.Pressed) -> None:
    haddock.chieftain.mail_event(self.event)
