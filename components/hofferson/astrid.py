from components.base import EventEmitButton
from . import Dialogue, Story, Prompt

class Character:
  character = ""
  line = ""
  actions = []

  def __init__(self, character):
    super().__init__()

    self.character = character["speaker"]
    self.line = character["line"]
    self.actions = character["actions"]
  
  def mount_self(self, story: Story):
    prompt = Prompt()
    story.nodes.append(Dialogue(self.character, self.line))
    story.nodes.append(prompt)
    story.refresh(recompose=True)
    for action in self.actions:
      prompt.options.append(EventEmitButton(action["line"], action["signal"]))