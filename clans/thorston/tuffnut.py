from typing import Type
import haddock
from librarians.core import get_save_files


class TitleScreen(haddock.State):
    @staticmethod
    def tag() -> str:
        return "clans.thorston.TitleScreen"

    @classmethod
    def _deserialize(
        cls: type["TitleScreen"],
        data: haddock.JSONValue,
        version: int,
    ) -> "TitleScreen":
        return cls()

    def _serialize(self) -> str:
        return ""

    @property
    def version(self) -> int:
        return 1


class SaveGameList(haddock.State):
    @staticmethod
    def tag() -> str:
        return "clans.thorston.SaveGameList"

    @classmethod
    def _deserialize(
        cls: type["SaveGameList"],
        data: haddock.JSONValue,
        version: int,
    ) -> "SaveGameList":
        return cls()

    def _serialize(self) -> str:
        return ""

    @property
    def version(self) -> int:
        return 1


class CreateGame(haddock.State):
    @staticmethod
    def tag() -> str:
        return "clans.thorston.CreateGame"

    @classmethod
    def _deserialize(
        cls: type["CreateGame"],
        data: haddock.JSONValue,
        version: int,
    ) -> "CreateGame":
        return cls()

    def _serialize(self) -> str:
        return ""

    @property
    def version(self) -> int:
        return 1


class TitleScreenRenderCommand(haddock.RenderCommand):
    pass


class TitleScreenRider(haddock.StateRider[TitleScreen]):
    state_type = TitleScreen

    def roll_call(self, state: TitleScreen, event: haddock.Event) -> None:
        pass

    def render(self, state: TitleScreen) -> TitleScreenRenderCommand:
        return TitleScreenRenderCommand()


class SaveGameListRenderCommand(haddock.RenderCommand):
    saves: list[tuple[str, str]]

    def __init__(self, saves: list[tuple[str, str]]):
        self.saves = saves


class SaveGameListRider(haddock.StateRider[SaveGameList]):
    state_type = SaveGameList

    def roll_call(self, state: SaveGameList, event: haddock.Event) -> None:
        pass

    def render(self, state: SaveGameList) -> SaveGameListRenderCommand:
        return SaveGameListRenderCommand(get_save_files())


class CreateGameRenderCommand(haddock.RenderCommand):
    pass

class CreateGameRider(haddock.StateRider[CreateGame]):
    state_type = CreateGame

    def roll_call(self, state: CreateGame, event: haddock.Event) -> None:
        pass

    def render(self, state: CreateGame) -> CreateGameRenderCommand:
        return CreateGameRenderCommand()


riders: haddock.Riders = [
    TitleScreenRider(),
    SaveGameListRider(),
    CreateGameRider(),
]
chiefs: haddock.Chiefs = []
