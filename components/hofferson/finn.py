from components.base import EventEmitButton
from . import Paragraph, Prompt, Story

class Location:
  location_id = ""
  location_ambient = ""
  location_actions = []

  def __init__(self, location):
    super().__init__()

    self.location_id = location["location"]
    self.location_ambient = location["ambient"]
    self.location_actions = location["actions"]
  
  def mount_self(self, story: Story):
    prompt = Prompt()
    story.nodes.append(Paragraph(self.location_ambient))
    story.nodes.append(prompt)
    story.refresh(recompose=True)
    for action in self.location_actions:
      prompt.options.append(EventEmitButton(action["line"], action["signal"]))