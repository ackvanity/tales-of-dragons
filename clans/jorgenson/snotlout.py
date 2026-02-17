import ast
from dataclasses import dataclass
from typing import List, Tuple
import haddock
from dragonic.interactions import send_dialogue, send_pause, send_prompt, send_story, DialogueResult, add_character_hook, add_location_hook
import uuid
from clans.hofferson import finn, astrid
from typing import Any

# Raise to suspend the Dragonic script at any location
class InterceptedCallException(Exception):
    pass

class ReturnDataEvent(haddock.Event):
    data: Any
    script: str

    def __init__(self, data, script):
        self.data = data
        self.script = script

class SendPromptEvent(haddock.EngineEvent):
    options: list[str]
    script: str # The Dragonic script triggering this call

    def __init__(self, options, script) -> None:
        self.options = options
        self.script = script

class SendPromptEventRider(haddock.EventRider[SendPromptEvent]):
    event_type = SendPromptEvent

    def roll_call(self, event: SendPromptEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Prompt([(option, haddock.EventSeries([ReturnDataEvent(DialogueResult(i, option), event.script), haddock.PopStateEvent()])) for i, option in enumerate(event.options)], event.script)))

class Prompt(haddock.State):
    options: list[tuple[str, haddock.Event]]
    script: str

    def __init__(self, options=None, script=None):
        print(f"Making prompt state: {options}")
        if options is None:
            options = []

        self.options = options
        self.script = script # type: ignore

class PromptRenderCommand(haddock.RenderCommand):
    options: list[tuple[str, haddock.Event]]

class PromptRider(haddock.StateRider[Prompt]):
    state_type = Prompt

    def roll_call(self, state: Prompt, event: haddock.Event) -> None:
        pass

    def render(self, state: Prompt) -> haddock.RenderCommand:
        command = PromptRenderCommand()
        command.options = state.options

        return command

class PromptRenderChief(haddock.RenderChief[PromptRenderCommand]):
    command_type = PromptRenderCommand

    def render(self, command: PromptRenderCommand, application) -> None:
        application.send_prompt(command.options)

class SendDialogueEvent(haddock.EngineEvent):
    character: str
    line: str
    script: str # The Dragonic script triggering this call

    def __init__(self, character, line, script) -> None:
        self.character = character
        self.line = line
        self.script = script

class SendDialogueEventRider(haddock.EventRider[SendDialogueEvent]):
    event_type = SendDialogueEvent

    def roll_call(self, event: SendDialogueEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Dialogue(event.character, event.line, event.script)))


class Dialogue(haddock.State):
    character: str
    line: str
    script: str

    def __init__(self, character, line, script):
        self.character = character
        self.line = line
        self.script = script

class DialogueRenderCommand(haddock.RenderCommand):
    character: str
    line: str
    script: str

class DialogueRider(haddock.StateRider[Dialogue]):
    state_type = Dialogue

    def roll_call(self, state: Dialogue, event: haddock.Event) -> None:
        pass

    def render(self, state: Dialogue) -> haddock.RenderCommand:
        command = DialogueRenderCommand()
        command.line = state.line
        command.character = state.character
        command.script = state.script

        return command

class DialogueRenderChief(haddock.RenderChief[DialogueRenderCommand]):
    command_type = DialogueRenderCommand

    def render(self, command: DialogueRenderCommand, application) -> None:
        application.send_dialogue(command.character, command.line)
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())

class SendStoryEvent(haddock.EngineEvent):
    line: str
    script: str # The Dragonic script triggering this call

    def __init__(self, line, script) -> None:
        self.line = line
        self.script = script

class SendStoryEventRider(haddock.EventRider[SendStoryEvent]):
    event_type = SendStoryEvent

    def roll_call(self, event: SendStoryEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(Story(event.line, event.script)))


class Story(haddock.State):
    line: str
    script: str

    def __init__(self, line, script):
        self.line = line
        self.script = script

class StoryRenderCommand(haddock.RenderCommand):
    line: str
    script: str

class StoryRider(haddock.StateRider[Story]):
    state_type = Story

    def roll_call(self, state: Story, event: haddock.Event) -> None:
        pass

    def render(self, state: Story) -> haddock.RenderCommand:
        command = StoryRenderCommand()
        command.line = state.line
        command.script = state.script

        return command

class StoryRenderChief(haddock.RenderChief[StoryRenderCommand]):
    command_type = StoryRenderCommand

    def render(self, command: StoryRenderCommand, application) -> None:
        application.send_story(command.line)
        haddock.chieftain.mail_event(ReturnDataEvent(None, command.script))
        haddock.chieftain.mail_event(haddock.PopStateEvent())

Block = Tuple[list[ast.stmt], int]

@dataclass
class DragonicState(haddock.State):
    block_stack: List[Block]
    locals: dict
    await_target: str | None = None

class DragonicQuest(haddock.Entity):
    def __init__(self, source: str, state=None):
        mod = ast.parse(source)
        self.body = mod.body
        
        if state is None:
            state = DragonicState(
                block_stack=[(self.body, 0)],
                locals={}
            )

        self.state = state
        self.result = None
        self.has_result = False
        self.waiting = False

        self.id = str(uuid.uuid4())

        self.state.locals["add_character_hook"] = add_character_hook
        self.state.locals["send_dialogue"] = send_dialogue
        self.state.locals["send_prompt"] = send_prompt
        self.state.locals["send_story"] = send_story
        self.state.locals["player"] = haddock.chieftain.call_entity(haddock.EntityID("jorgenson", "player", "player"))

    def run(self):
        if self.waiting and not self.has_result:
            return
        
        try:
            state = self.state

            locals_ = dict(state.locals)

            while state.block_stack:
                block, i = state.block_stack[-1]

                # finished this block → return to parent
                if i >= len(block):
                    state.block_stack.pop()
                    continue

                stmt = block[i]

                # advance instruction pointer
                state.block_stack[-1] = (block, i + 1)

                if isinstance(stmt, ast.Assign):
                    value = self._eval_expr(stmt.value, locals_)

                    self._assign(stmt.targets[0], value, locals_)

                elif isinstance(stmt, ast.Expr):
                    self._eval_expr(stmt.value, locals_)

                elif isinstance(stmt, ast.If):
                    cond = self._eval_expr(stmt.test, locals_)
                    branch = stmt.body if cond else stmt.orelse

                    # push chosen branch as a new execution block
                    state.block_stack.append((branch, 0))

                else:
                    raise NotImplementedError(
                        f"Unsupported statement: {type(stmt)}"
                    )
        except InterceptedCallException:
            # Unroll the last function call if intercepted
            state = self.state
            block, i = state.block_stack[-1]
            state.block_stack[-1] = (block, i - 1)
    
    def _eval_expr(self, expr, locals_):
        if isinstance(expr, ast.Call):
            return self._eval_call(expr, locals_)
        elif isinstance(expr, ast.Constant):
            return expr.value
        elif isinstance(expr, ast.Name):
            return locals_[expr.id]
        elif isinstance(expr, ast.Attribute):
            obj = self._eval_expr(expr.value, locals_)
            return getattr(obj, expr.attr)
        else:
            # fallback only if you truly don't care
            return eval(
                compile(ast.Expression(expr), "<dragonic>", "eval"),
                {},
                locals_
            )

    def _eval_call(self, call: ast.Call, locals_):
        func = self._eval_expr(call.func, locals_)
        args = [self._eval_expr(a, locals_) for a in call.args]
        kwargs = {
            kw.arg: self._eval_expr(kw.value, locals_)
            for kw in call.keywords
        }

        # INTERCEPT HERE
        if func is add_character_hook:
            assert len(args) >= 2

            character = args[0]
            line = args[1]
            line_id = str(uuid.uuid4())
            event = haddock.EventSeries([astrid.RemoveDialogueEvent(character, line_id), ReturnDataEvent(None, self.id)])

            return self._intercept_call(astrid.AddDialogueEvent(character, line, event, line_id))

        if func is send_dialogue:
            assert len(args) >= 2

            character = args[0]
            line = args[1]
            
            return self._intercept_call(SendDialogueEvent(character, line, self.id))
        
        if func is send_prompt:
            assert len(args) >= 1

            options = args[0]

            print("Need to add options: ", options)

            return self._intercept_call(SendPromptEvent(options, self.id))

        if func is send_story:
            assert len(args) >= 1

            line = args[0]

            return self._intercept_call(SendStoryEvent(line, self.id))

        # otherwise, normal Python call
        print(f"Local dump {locals_}")
        return eval(
            compile(ast.Expression(call), "<dragonic>", "eval"),
            {},
            locals_
        )

    def _intercept_call(self, event: haddock.Event):
        if not self.has_result:
            haddock.chieftain.mail_event(event)
            
            self.waiting = True
            raise InterceptedCallException()
        
        self.waiting = False
        self.has_result = False
        print(f"Returning result {self.result}")
        return self.result

    def _assign(self, target: ast.expr, value, locals_):
        if isinstance(target, ast.Name):
            print("Assign", target, target.id, value, locals_)
            locals_[target.id] = value

        elif isinstance(target, ast.Attribute):
            obj = self._eval_expr(target.value, locals_)
            setattr(obj, target.attr, value)

        else:
            raise NotImplementedError(
                f"Unsupported assignment target: {type(target)}"
            )

class DragonicQuestRider(haddock.EntityRider[DragonicQuest]):
    entity_type = DragonicQuest

    def roll_call(self, entity: DragonicQuest, event: haddock.Event) -> None:
        if isinstance(event, ReturnDataEvent) and event.script == entity.id:
            print(f"Script got return data {event.data}")
            entity.has_result = True
            entity.result = event.data
            entity.run()
        if isinstance(event, haddock.TeamAssmebled):
            entity.run()
            print("Ran the script!")

riders: haddock.Riders = [PromptRider(), DialogueRider(), StoryRider(), DragonicQuestRider(), SendPromptEventRider(), SendDialogueEventRider(), SendStoryEventRider()]
chiefs: haddock.Chiefs = [PromptRenderChief(), DialogueRenderChief(), StoryRenderChief()]