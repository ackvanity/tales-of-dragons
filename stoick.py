"""
stoick.py — Textual application shell (View entry point).

Implements haddock.Application using Textual, providing the UI container
and helper methods used by RenderChiefs to mount widgets asynchronously.
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.containers import VerticalGroup
import haddock

from components.hofferson import Story


class TextualApplication(App):
    """
    The main Textual application.

    Serves as the View entry point. Provides a single root mount point
    (#application) into which RenderChiefs mount their widgets.

    Registered as a virtual subclass of haddock.Application so it satisfies
    the Application ABC without inheriting its metaclass directly.
    """

    CSS_PATH = "./tcss/stoick.tcss"

    def compose(self) -> ComposeResult:
        """Build the base UI layout: header, content area, footer."""
        yield Header()
        yield VerticalGroup(id="application")
        yield Footer()

    def get_mount_point(self):
        """Return the #application container that holds all game content."""
        return self.query_one("#application")

    def get_story(self) -> Story | None:
        """
        Return the active Story widget if one is currently mounted.

        Returns None if the mount point is empty or the first child is not a Story.
        """
        children = self.get_mount_point().children
        if children and isinstance(children[0], Story):
            return children[0]
        return None

    async def clear_history(self) -> None:
        """Remove all widgets from the mount point."""
        for child in list(self.get_mount_point().children):
            await child.remove()

    async def ensure_singleton(self, klass: type) -> None:
        """
        Ensure exactly one widget of type klass is mounted.

        If the mount point already contains exactly one widget of the correct
        type, does nothing. Otherwise clears the mount point and mounts a
        new instance of klass.
        """
        mount_point = self.get_mount_point()
        children = list(mount_point.children)
        if len(children) != 1 or type(children[0]) != klass:
            await self.clear_history()
            await mount_point.mount(klass())

    def on_mount(self) -> None:
        """Fire TeamAssembled to start the engine after the UI is ready."""
        haddock.chieftain.mail_event(haddock.TeamAssembled())


# Register as a virtual subclass of Application so isinstance checks pass
# without the metaclass conflict that direct inheritance would cause.
haddock.Application.register(TextualApplication)
