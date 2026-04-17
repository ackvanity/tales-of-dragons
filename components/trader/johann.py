import haddock
from clans.trader.johann import FishingRenderCommand, Biome, fishes, select_fish
from textual.containers import CenterMiddle
from components.base import TCSS, EventEmitButton
from clans.ingerman import fishlegs
import asyncio
from textual.widgets import Label, Button


class Fishing(CenterMiddle, TCSS):
    biome: Biome
    ambient: str

    def __init__(self, biome: Biome, ambient: str):
        self.biome = biome
        self.ambient = ambient
        super().__init__()

    def compose(self):
        yield Label("Fishing")
        yield Label(self.biome)
        yield Label(self.ambient)
        yield Button("Fetch a fish", id="fish")
        yield EventEmitButton("Go Back.", haddock.PopStateEvent())

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "fish":
            fish = select_fish(
                [fish for fish in fishes if fish.biome_freshwater]
            )
            satchel: fishlegs.Satchel = haddock.chieftain.call_entity(fishlegs.get_satchel(haddock.EntityID("jorgenson", "player", "player")))  # type: ignore
            added = satchel.add_item(fish)

            if not added:
                self.notify(
                    "Uh, I can't fit the fish in my satchel... I guess you'll live on, for today."
                )
            else:
                self.notify("Well, let's see the catch.")


class FishingRenderChief(haddock.RenderChief[FishingRenderCommand]):
    command_type = FishingRenderCommand

    def render(self, command: FishingRenderCommand, application) -> None:
        async def _render() -> None:
            await application.clear_history()
            await application.get_mount_point().mount(
                Fishing(command.biome, command.ambient)
            )

        asyncio.create_task(_render())
