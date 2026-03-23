import asyncio
import haddock
from clans.hofferson.astrid import TalkingRenderCommand
from components.base import EventEmitButton
from . import Dialogue, Story, Prompt
from stoick import TextualApplication


class Character:
  def __init__(self, command: TalkingRenderCommand):
    self.speaker = command.speaker
    self.line = command.line
    self.actions = command.actions

  def mount_self(self, story: Story):
    prompt = Prompt()
    story.nodes.append(Dialogue(self.speaker, self.line))
    story.nodes.append(prompt)
    story.refresh(recompose=True)
    for action in self.actions:
      prompt.options.append(EventEmitButton(action.line, action.signal))



class TalkingRenderChief(haddock.RenderChief[TalkingRenderCommand]):
  command_type = TalkingRenderCommand

  def render(self, command: TalkingRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.ensure_singleton(Story)
      story = application.get_story()
      if story is not None:
        Character(command).mount_self(story)

    asyncio.create_task(_render())
