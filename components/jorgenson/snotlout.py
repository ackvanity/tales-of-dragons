import asyncio
import haddock
from clans.jorgenson.snotlout import (
  PromptRenderCommand,
  DialogueRenderCommand,
  StoryRenderCommand,
  ReturnDataEvent,
)
from components.base import EventEmitButton
from components.hofferson import Story, Prompt, Dialogue, Paragraph
from stoick import TextualApplication


class PromptRenderChief(haddock.RenderChief[PromptRenderCommand]):
  command_type = PromptRenderCommand

  def render(self, command: PromptRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.ensure_singleton(Story)
      story = application.get_story()
      if story is not None:
        prompt = Prompt()
        for label, event in command.options:
          prompt.options.append(EventEmitButton(label, event))
        story.nodes.append(prompt)
        story.refresh(recompose=True)

    asyncio.create_task(_render())


class DialogueRenderChief(haddock.RenderChief[DialogueRenderCommand]):
  command_type = DialogueRenderCommand

  def render(self, command: DialogueRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.ensure_singleton(Story)
      story = application.get_story()
      if story is not None:
        story.nodes.append(Dialogue(command.character, command.line))
        story.refresh(recompose=True)

    asyncio.create_task(_render())
    haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
    haddock.chieftain.mail_event(haddock.PopStateEvent())


class StoryRenderChief(haddock.RenderChief[StoryRenderCommand]):
  command_type = StoryRenderCommand

  def render(self, command: StoryRenderCommand, application: TextualApplication) -> None:
    async def _render():
      await application.ensure_singleton(Story)
      story = application.get_story()
      if story is not None:
        story.nodes.append(Paragraph(command.line))
        story.refresh(recompose=True)

    asyncio.create_task(_render())
    haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
    haddock.chieftain.mail_event(haddock.PopStateEvent())
