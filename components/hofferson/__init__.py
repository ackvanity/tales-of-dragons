from textual.app import ComposeResult
from textual.widgets import Label
from textual.widget import Widget
from textual.containers import HorizontalGroup, VerticalScroll, VerticalGroup
from textual.reactive import reactive
from typing import List

class Dialogue(HorizontalGroup):
  speaker: reactive[str] = reactive("")
  line: reactive[str] = reactive("")
  
  def __init__(self, speaker, line):
    super().__init__()

    self.speaker = speaker
    self.line = line
  
  def compose(self) -> ComposeResult:
    yield Label(self.speaker)
    yield Label(self.line)

class Paragraph(Label):
  pass

class Story(VerticalScroll):
  nodes: reactive[List[Widget]] 
  
  def __init__(self):
    super().__init__()
    self.nodes = []

  def compose(self) -> ComposeResult:
    yield Label("COMPOSE")

    print("COMPOSE", self.nodes)
    for node in self.nodes:
      print(node, isinstance(node, Prompt))
      if not isinstance(node, Prompt):
        yield node

    if len(self.nodes) and isinstance(self.nodes[-1], Prompt):
      yield self.nodes[-1]

class Prompt(VerticalGroup):
  options: reactive[List[Widget]] 
  
  def __init__(self):
    super().__init__()
    self.options = []

  def compose(self) -> ComposeResult:
    for option in self.options:
      yield option