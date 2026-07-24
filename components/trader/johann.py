import haddock
from clans.trader.johann import FishingRenderCommand

class FishingRenderChief(haddock.RenderChief[FishingRenderCommand]):
    command_type = FishingRenderCommand

    def render(self, command: FishingRenderCommand, application) -> None:
        application.send_data("fishing", [command.biome, command.ambient])
