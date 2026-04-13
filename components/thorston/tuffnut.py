from textual.app import ComposeResult

from clans.thorston.tuffnut import (
    TitleScreenRenderCommand,
    SaveGameList as SaveGameListState,
    SaveGameListRenderCommand,
    CreateGame as CreateGameState,
    CreateGameRenderCommand,
)
from components.hofferson.astrid import Dialogue
from textual.containers import CenterMiddle, Center
import haddock
import asyncio
from components.base import TCSS, EventEmitButton
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input


class TitleScreen(CenterMiddle, TCSS):
    def compose(self) -> ComposeResult:
        yield Label("Tales of")
        yield Label("Dragons")
        with Center():
            yield EventEmitButton(
                "Start Game",
                haddock.AppendStateEvent(SaveGameListState()),
                id="start_game",
            )


class TitleScreenRenderChief(haddock.RenderChief[TitleScreenRenderCommand]):
    command_type = TitleScreenRenderCommand

    def render(self, command: TitleScreenRenderCommand, application) -> None:
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(TitleScreen())

        asyncio.create_task(_render())


class SaveGameList(CenterMiddle, TCSS):
    def compose(self) -> ComposeResult:
        yield Label("So, whose adventure will you continue?", id="title")
        yield EventEmitButton(
            "New Viking",
            haddock.AppendStateEvent(CreateGameState()),
            id="new_viking",
        )
        yield EventEmitButton("Back", haddock.PopStateEvent(), id="back")


class SaveGameListRenderChief(haddock.RenderChief[SaveGameListRenderCommand]):
    command_type = SaveGameListRenderCommand

    def render(self, command: SaveGameListRenderCommand, application) -> None:
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(SaveGameList())

        asyncio.create_task(_render())


class CreateGame(CenterMiddle, TCSS):
    def compose(self) -> ComposeResult:
        yield Dialogue("???", "Hi there. Uh, who *are* you?")
        yield (widget := Input(id="name"))
        yield Button("Hi, nice to meet you!", id="submit")
        self.widget = widget

    def on_button_pressed(self, event: Button.Pressed) -> None:
        start_game_func(self.widget.value)


class CreateGameRenderChief(haddock.RenderChief[CreateGameRenderCommand]):
    command_type = CreateGameRenderCommand

    def render(self, command: CreateGameRenderCommand, application) -> None:
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(CreateGame())

        asyncio.create_task(_render())

start_game_func = lambda n: None