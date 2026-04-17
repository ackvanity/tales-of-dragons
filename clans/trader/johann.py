import haddock
from clans.ingerman import fishlegs
from typing import Literal, Type, List
import random

fishes: List[Type["Fish"]] = []


def select_fish(fishes: List[Type["Fish"]]):
    cls = random.choices(
        fishes, weights=[fish.proba_weight for fish in fishes], k=1
    )[0]
    return cls()


class Fish(fishlegs.BaseItem):

    name: str = "Fish"
    description: str = (
        "A nice, fresh fish to stave you and your dragon's hunger."
    )
    energy: int = 1
    happiness: int = 1
    biome_freshwater: bool = False  # Freshwater biomes, like lakes and rivers
    biome_coastal: bool = False  # Coastal salt water, like beaches
    biome_sea: bool = False  # Shallow seas far from shore, like oceans
    biome_deep_sea: bool = False  # Deep ends of the sceans
    proba_weight: float = 1.0  # Weight to use

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        fishes.append(cls)


class Salmon(Fish):
    name: str = "Salmon"
    description: str = (
        "A raw salmon. It's great eaten raw, greater when cooked."
    )

    biome_coastal = True
    biome_freshwater = True

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["Salmon"], data: haddock.JSONValue, version: int
    ) -> "Salmon":
        return cls()

    @staticmethod
    def tag() -> str:
        return "trader.johann.Salmon"


class Tuna(Fish):
    name: str = "Tuna"
    description: str = "A stone-cold tuna. Delicious even when frozen solid."
    biome_coastal: bool = True
    biome_sea: bool = True

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["Tuna"], data: haddock.JSONValue, version: int
    ) -> "Tuna":
        return cls()

    @staticmethod
    def tag() -> str:
        return "trader.johann.Tuna"


class Cod(Fish):
    name: str = "Cod"
    description: str = "A cod."
    biome_freshwater: bool = True
    biome_coastal: bool = True
    biome_sea: bool = True

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["Cod"], data: haddock.JSONValue, version: int
    ) -> "Cod":
        return cls()

    @staticmethod
    def tag() -> str:
        return "trader.johann.Cod"


class Eel(Fish):
    name: str = "Eel"
    description: str = (
        "An eel! It's not exactly the most enticing meal ever and who knows what health hazards it might have..."
    )
    biome_freshwater: bool = True
    biome_coastal: bool = True
    biome_sea: bool = True
    biome_deep_sea: bool = True

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["Eel"], data: haddock.JSONValue, version: int
    ) -> "Eel":
        return cls()

    @staticmethod
    def tag() -> str:
        return "trader.johann.Eel"


Biome = Literal["freshwater", "coastal", "sea", "deep_sea"]


class Fishing(haddock.State):
    biome: Biome
    ambient: str

    def __init__(self, biome: Biome, ambient: str):
        self.biome = biome
        self.ambient = ambient

    def _serialize(self) -> haddock.JSONValue:
        return [self.biome, self.ambient]

    @classmethod
    def _deserialize(
        cls: type["Fishing"], data: haddock.JSONValue, version: int
    ) -> "Fishing":
        if version > 1:
            raise haddock.DeserializeVersionUnsupportedException
        return cls(data[0], data[1])  # type: ignore

    @property
    def version(self) -> int:
        return 1

    @staticmethod
    def tag() -> str:
        return "trader.johann.Fishing"


class FishingRider(haddock.StateRider[Fishing]):
    state_type = Fishing

    def roll_call(self, state: Fishing, event: haddock.Event) -> None:
        pass

    def render(self, state: Fishing) -> haddock.RenderCommand:
        return FishingRenderCommand(state.biome, state.ambient)


class FishingRenderCommand(haddock.RenderCommand):
    biome: Biome
    ambient: str

    def __init__(self, biome: Biome, ambient: str):
        self.biome = biome
        self.ambient = ambient


riders: haddock.Riders = [FishingRider()]
chiefs: haddock.Chiefs = []
