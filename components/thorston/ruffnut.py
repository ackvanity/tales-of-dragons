import haddock
from clans.thorston.ruffnut import RuffnutInitiationRenderCommand
from clans.jorgenson.snotlout import ReturnDataEvent


class RuffnutInitiationStateRenderChief(
    haddock.RenderChief[RuffnutInitiationRenderCommand]
):
    command_type = RuffnutInitiationRenderCommand

    def render(
        self, command: RuffnutInitiationRenderCommand, application
    ) -> None:
        haddock.chieftain.mail_event(haddock.PopStateEvent())
        haddock.chieftain.mail_event(ReturnDataEvent(None, "meet_hiccup"))
        # pass
