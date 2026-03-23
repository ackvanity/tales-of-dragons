import asyncio
import haddock
from clans.hofferson.finn import WanderingRenderCommand
from components.base import EventEmitButton
from . import Paragraph, Prompt, Story
from stoick import TextualApplication


class Location:
  def __init__(self, command: WanderingRenderCommand):
    self.location_id = command.id
    self.location_ambient = command.ambient
    self.location_actions = command.actions

  def mount_self(self, story: Story):
    prompt = Prompt()
    story.nodes.append(Paragraph(self.location_ambient))
    story.nodes.append(prompt)
    story.refresh(recompose=True)
    for action in self.location_actions:
      prompt.options.append(EventEmitButton(action.line, action.signal))


class WanderingRenderChief(haddock.RenderChief[WanderingRenderCommand]):
  command_type = WanderingRenderCommand

  def render(self, command: WanderingRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.ensure_singleton(Story)
      story = application.get_story()
      if story is not None:
        Location(command).mount_self(story)

    asyncio.create_task(_render())
