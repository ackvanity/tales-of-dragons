import haddock
from clans.jorgenson import snotlout


class RuffnutInitiationState(haddock.State):
    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["RuffnutInitiationState"],
        data: haddock.JSONValue,
        version: int,
    ) -> "RuffnutInitiationState":
        return cls()

    @staticmethod
    def tag() -> str:
        return "clans.thorston.RuffnutInitiationState"

    @property
    def version(self) -> int:
        return 1


class RuffnutInitiationRenderCommand(haddock.RenderCommand):
    pass


class RuffnutInitiationStateRider(haddock.StateRider[RuffnutInitiationState]):
    state_type = RuffnutInitiationState

    def render(self, state: RuffnutInitiationState) -> haddock.RenderCommand:
        return RuffnutInitiationRenderCommand()

    def roll_call(
        self, state: RuffnutInitiationState, event: haddock.Event
    ) -> None:
        # if isinstance(event, haddock.TeamAssembled):
        #     haddock.chieftain.mail_event(snotlout.ReturnDataEvent(None, "meet_hiccup"))
        pass


riders: haddock.Riders = [RuffnutInitiationStateRider()]
chiefs: haddock.Chiefs = []
