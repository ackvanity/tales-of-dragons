"""
components/base.py — Shared base widget for the View layer.

Provides EventEmitButton, the fundamental interactive widget that bridges
Textual's button press events to the haddock engine event system.
"""

from textual.widgets import Button
from textual.reactive import reactive
from librarians.tcss import load_tcss_file
import haddock


class TCSS:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        module = "/".join(cls.__module__.split(".")[1:])
        name = cls.__name__

        cls.DEFAULT_CSS = load_tcss_file(module, name)


class EventEmitButton(Button, TCSS):
    """
    A Textual Button that fires a haddock.Event when pressed.

    Used throughout the View layer wherever the player needs to make
    a selection. The event is set at construction time and fired via
    haddock.chieftain.mail_event() on press.

    Attributes:
        event: The haddock Event to fire when this button is pressed.
    """

    event: reactive[haddock.Event] = reactive(haddock.Event())

    def __init__(
        self,
        line: str = "",
        haddock_event: haddock.Event = haddock.Event(),
        *args,
        **kwargs,
    ) -> None:
        """
        Args:
            line:          The button label shown to the player.
            haddock_event: The event to fire when the button is pressed.
        """
        super().__init__(line, *args, **kwargs)
        self.event = haddock_event

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Forward the button press to the haddock engine as a game event."""
        haddock.chieftain.mail_event(self.event)
