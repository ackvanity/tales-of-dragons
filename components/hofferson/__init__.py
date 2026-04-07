"""
components/hofferson/__init__.py — Core story widgets for the hofferson View layer.

Defines the Textual widgets that make up the narrative display: the scrolling
Story container, individual Dialogue lines, Paragraph narration text, and the
Prompt action menu that the player interacts with.

These widgets are mounted and composed by the hofferson RenderChiefs.
"""

from textual.app import ComposeResult
from textual.widgets import Label
from textual.widget import Widget
from textual.containers import HorizontalGroup, VerticalScroll, VerticalGroup
from textual.reactive import reactive
from typing import List
from components.base import EventEmitButton, TCSS


class Dialogue(HorizontalGroup, TCSS):
    """
    A single line of character dialogue displayed as "Speaker  Line".

    Laid out horizontally with the speaker name on the left and the
    line of dialogue on the right.

    Attributes:
        speaker: The character's display name.
        line:    The dialogue text.
    """

    speaker: reactive[str] = reactive("")
    line: reactive[str] = reactive("")

    def __init__(self, speaker: str, line: str) -> None:
        super().__init__()
        self.speaker = speaker
        self.line = line

    def compose(self) -> ComposeResult:
        yield Label(self.speaker, classes="speaker")
        yield Label(self.line, classes="line")


class Paragraph(Label, TCSS):
    """
    A narration paragraph with no attributed speaker.

    Used for story beats and ambient descriptions.
    """


class Story(VerticalScroll, TCSS):
    """
    The main scrolling content container that accumulates narrative nodes.

    Nodes (Dialogue, Paragraph, Prompt) are appended to the nodes list
    by RenderChiefs and composed in order. Prompts are always rendered
    last; only the most recent Prompt is displayed.

    Attributes:
        nodes: Ordered list of widgets to render. Mutated externally by
               RenderChiefs, then story.refresh(recompose=True) is called
               to trigger a redraw.
    """

    nodes: reactive[List[Widget]]

    def __init__(self) -> None:
        super().__init__()
        self.nodes = []

    def compose(self) -> ComposeResult:
        """
        Render all non-Prompt nodes in order, then the final Prompt (if any).

        Prompts are excluded from the middle of the list so they always
        appear at the bottom of the scroll view.
        """
        for node in self.nodes:
            if not isinstance(node, Prompt):
                yield node

        if self.nodes and isinstance(self.nodes[-1], Prompt):
            yield self.nodes[-1]


class Prompt(VerticalGroup, TCSS):
    """
    A vertically stacked group of EventEmitButtons for player choices.

    Options are appended to the options list by RenderChiefs after the
    widget is created, then story.refresh(recompose=True) triggers a redraw.

    Attributes:
        options: List of EventEmitButton widgets, one per choice.
    """

    options: reactive[List[EventEmitButton]]

    def __init__(self) -> None:
        super().__init__()
        self.options = []

    def compose(self) -> ComposeResult:
        for option in self.options:
            yield option
