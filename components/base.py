"""
components/base.py — Shared base widget for the View layer.

Provides EventEmitButton, the fundamental interactive widget that bridges
Textual's button press events to the haddock engine event system.
"""

from textual.widgets import Button
from textual.reactive import reactive
import haddock


class EventEmitButton(Button):
    """
    A Textual Button that fires a haddock.Event when pressed.

    Used throughout the View layer wherever the player needs to make
    a selection. The event is set at construction time and fired via
    haddock.chieftain.mail_event() on press.

    Attributes:
        event: The haddock Event to fire when this button is pressed.
    """

    event: reactive[haddock.Event] = reactive(haddock.Event())

    def __init__(self, line: str = "", haddock_event: haddock.Event = haddock.Event()) -> None:
        """
        Args:
            line:          The button label shown to the player.
            haddock_event: The event to fire when the button is pressed.
        """
        super().__init__(line)
        self.event = haddock_event

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Forward the button press to the haddock engine as a game event."""
        haddock.chieftain.mail_event(self.event)
