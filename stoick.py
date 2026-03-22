from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.containers import VerticalGroup
import haddock

from components.hofferson import Story


class TextualApplication(App):
  def compose(self) -> ComposeResult:
    yield Header()
    yield VerticalGroup(id="application")
    yield Footer()

  def get_mount_point(self):
    return self.query_one("#application")

  def get_story(self) -> Story | None:
    children = self.get_mount_point().children
    if children and isinstance(children[0], Story):
      return children[0]
    return None

  async def clear_history(self):
    for child in list(self.get_mount_point().children):
      await child.remove()

  async def ensure_singleton(self, klass: type):
    mount_point = self.get_mount_point()
    children = list(mount_point.children)
    if len(children) != 1 or type(children[0]) != klass:
      await self.clear_history()
      await mount_point.mount(klass())

  def on_mount(self) -> None:
    haddock.chieftain.mail_event(haddock.TeamAssembled())


haddock.Application.register(TextualApplication)
