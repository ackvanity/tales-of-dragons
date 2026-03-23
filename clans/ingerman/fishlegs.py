"""
clans/ingerman/fishlegs.py — Inventory system.

Manages item entities (BaseItem, Item, NoItem), Satchel entities (inventory
containers), and the UI states for browsing them (SatchelsList, SatchelItems).

Also injects a "Check satchel" action into all NPC dialogue menus via the
module-level extra_character_actions list.
"""

import haddock
from clans.hofferson import Action


# ---------------------------------------------------------------------------
# Item entities
# ---------------------------------------------------------------------------

class BaseItem(haddock.Entity):
    """
    Abstract base for all item types stored in a Satchel.

    Subclasses must set name and description as class attributes or
    instance attributes, and implement the full Entity serialization
    interface (version, _serialize, _deserialize, tag).

    serialize() is overridden here to include the tag so that the item
    type registry can reconstruct the correct subclass on deserialization.
    """

    name: str
    description: str

    def serialize(self) -> haddock.JSONValue:
        """Return {"tag": ..., "payload": [version, _serialize()]} for type-tagged storage."""
        return {"tag": self.tag(), "payload": [self.version, self._serialize()]}


class Item(BaseItem):
    """A generic placeholder item with no special behaviour."""

    name: str = "Item"
    description: str = "A generic item. Nobody knows what it is useful for..."

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(cls: type["Item"], data: haddock.JSONValue, version: int) -> "Item":
        return cls()

    @staticmethod
    def tag() -> str:
        return "ingerman.Item"


class NoItem(BaseItem):
    """
    Sentinel used to fill empty satchel slots in the UI.

    Serializes to an empty string since it carries no state.
    """

    name: str = "Empty Slot"
    description: str = "No items here..."

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(cls: type["NoItem"], data: haddock.JSONValue, version: int) -> "NoItem":
        return cls()

    @staticmethod
    def tag() -> str:
        return "ingerman.NoItem"


# ---------------------------------------------------------------------------
# Satchel entity
# ---------------------------------------------------------------------------

class Satchel(haddock.Entity):
    """
    An inventory container holding up to capacity items.

    Stored in Hiccup.entities as EntityID("ingerman", "satchel", <id>).
    The owner field links the satchel to its owning entity (typically the player).

    Attributes:
        owner:    EntityID of the entity that owns this satchel.
        items:    Currently held items (may be shorter than capacity).
        capacity: Maximum number of items this satchel can hold.
    """

    owner: haddock.EntityID
    items: list[BaseItem]
    capacity: int = 10

    def __init__(
        self,
        items: list[BaseItem],
        capacity: int,
        owner: haddock.EntityID,
    ) -> None:
        self.items = items
        self.capacity = capacity
        self.owner = owner

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return {
            "owner": self.owner.serialize(),
            "capacity": self.capacity,
            "items": [item.serialize() for item in self.items],
        }

    @classmethod
    def _deserialize(cls: type["Satchel"], data: haddock.JSONValue, version: int) -> "Satchel":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict for Satchel, got {data!r}")
            owner = haddock.EntityID.deserialize(data["owner"])
            capacity = data["capacity"]
            items = [_deserialize_item(i) for i in data["items"]]  # type: ignore
            return cls(items, capacity, owner)  # type: ignore
        raise haddock.DeserializeVersionUnsupportedException()

    @staticmethod
    def tag() -> str:
        return "ingerman.Satchel"


# ---------------------------------------------------------------------------
# Inventory UI states
# ---------------------------------------------------------------------------

class SatchelsList(haddock.State):
    """
    UI state showing a list of all satchels the player can open.

    Currently hardcoded to display the player's single satchel.
    Dismissed by CloseSatchelsListEvent.
    """

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return ""

    @classmethod
    def _deserialize(
        cls: type["SatchelsList"],
        data: haddock.JSONValue,
        version: int,
    ) -> "SatchelsList":
        return cls()

    @staticmethod
    def tag() -> str:
        return "ingerman.SatchelsList"


class SatchelItems(haddock.State):
    """
    UI state showing the contents of a specific satchel.

    Dismissed by CloseSatchelItemsEvent.

    Attributes:
        satchel: EntityID of the Satchel entity being viewed.
    """

    satchel: haddock.EntityID

    def __init__(self, satchel: haddock.EntityID) -> None:
        self.satchel = satchel

    @property
    def version(self) -> int:
        return 1

    def _serialize(self) -> haddock.JSONValue:
        return self.satchel.serialize()

    @classmethod
    def _deserialize(
        cls: type["SatchelItems"],
        data: haddock.JSONValue,
        version: int,
    ) -> "SatchelItems":
        if version == 1:
            return cls(haddock.EntityID.deserialize(data))
        raise haddock.DeserializeVersionUnsupportedException

    @staticmethod
    def tag() -> str:
        return "ingerman.SatchelItems"


# ---------------------------------------------------------------------------
# Render commands
# ---------------------------------------------------------------------------

class SatchelsListRenderCommand(haddock.RenderCommand):
    """
    Payload for rendering the satchel list screen.

    satchels is a list of (display name, open event) pairs, one per satchel.
    """

    satchels: list[tuple[str, haddock.Event]]

    def __init__(self, satchels: list[tuple[str, haddock.EntityID]]) -> None:
        self.satchels = [
            (name, OpenSatchelItemsEvent(get_satchel(owner)))
            for name, owner in satchels
        ]  # type: ignore


class SatchelItemsRenderCommand(haddock.RenderCommand):
    """
    Payload for rendering a single satchel's contents.

    items always has exactly capacity entries; empty slots are filled with NoItem.
    """

    title: str
    items: list[BaseItem]

    def __init__(self, title: str, items: list[BaseItem]) -> None:
        self.title = title
        self.items = items


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class OpenSatchelsEvent(haddock.EngineEvent):
    """Open the satchel list screen. Fired by the "Check satchel" action."""

    @staticmethod
    def tag() -> str:
        return "ingerman.OpenSatchelsEvent"


class OpenSatchelItemsEvent(haddock.EngineEvent):
    """Open the items view for a specific satchel."""

    satchel: haddock.EntityID

    def __init__(self, satchel: haddock.EntityID) -> None:
        self.satchel = satchel


class CloseSatchelsListEvent(haddock.Event):
    """Dismiss the satchel list screen (pop SatchelsList state)."""


class CloseSatchelItemsEvent(haddock.Event):
    """Dismiss the satchel items screen (pop SatchelItems state)."""


# ---------------------------------------------------------------------------
# Riders
# ---------------------------------------------------------------------------

class SatchelsListRider(haddock.StateRider[SatchelsList]):
    """Renders the satchel list and handles its close event."""

    state_type = SatchelsList

    def roll_call(self, state: SatchelsList, event: haddock.Event) -> None:
        if isinstance(event, CloseSatchelsListEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())

    def render(self, state: SatchelsList) -> haddock.RenderCommand:
        return SatchelsListRenderCommand([
            ("My satchel", haddock.EntityID("haddock", "player", "player"))
        ])


class SatchelItemsRider(haddock.StateRider[SatchelItems]):
    """Renders a satchel's contents and handles its close event."""

    state_type = SatchelItems

    def roll_call(self, state: SatchelItems, event: haddock.Event) -> None:
        if isinstance(event, CloseSatchelItemsEvent):
            haddock.chieftain.mail_event(haddock.PopStateEvent())

    def render(self, state: SatchelItems) -> haddock.RenderCommand:
        def no_default():
            raise Exception("Satchel was a ghost?")

        satchel: Satchel = haddock.chieftain.call_entity(state.satchel, no_default)  # type: ignore
        padded = satchel.items + [
            NoItem() for _ in range(satchel.capacity - len(satchel.items))
        ]
        return SatchelItemsRenderCommand(f"Satchel ({satchel.capacity} items)", padded)


class OpenSatchelsEventRider(haddock.EventRider[OpenSatchelsEvent]):
    """Push SatchelsList state when the player opens their inventory."""

    event_type = OpenSatchelsEvent

    def roll_call(self, event: OpenSatchelsEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(SatchelsList()))


class OpenSatchelItemsEventRider(haddock.EventRider[OpenSatchelItemsEvent]):
    """Push SatchelItems state for a specific satchel."""

    event_type = OpenSatchelItemsEvent

    def roll_call(self, event: OpenSatchelItemsEvent) -> None:
        haddock.chieftain.mail_event(haddock.AppendStateEvent(SatchelItems(event.satchel)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_satchel(owner: haddock.EntityID) -> haddock.EntityID:
    """
    Return the EntityID of the satchel owned by the given entity.

    Searches all ingerman/satchel entities. Raises if none found.
    """
    satchels = haddock.chieftain.call_entities("ingerman", "satchel", None)
    for id, satchel in satchels:
        if satchel.owner == owner:  # type: ignore
            return id
    raise Exception("No satchel?")


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

open_satchels_action = Action(
    line="Check satchel",
    signal=OpenSatchelsEvent(),
)
"""The "Check satchel" action injected into all NPC menus."""

extra_character_actions: list[Action] = [open_satchels_action]
"""Actions contributed by this module to every NPC dialogue menu."""

# ---------------------------------------------------------------------------
# Item type registry
# ---------------------------------------------------------------------------

_ITEM_REGISTRY: dict[str, type[BaseItem]] = {}
"""Maps item tag strings to BaseItem subclasses for deserialization."""


def _register_item(cls: type[BaseItem]) -> None:
    """Register a BaseItem subclass so it can be reconstructed by tag."""
    _ITEM_REGISTRY[cls.tag()] = cls


def _deserialize_item(data: haddock.JSONValue) -> BaseItem:
    """Reconstruct a BaseItem from its tagged serialized form.

    Expects {"tag": str, "payload": [version, inner_payload]}.
    Selects the correct subclass by tag, then calls its deserialize().
    """
    if not isinstance(data, dict) or "tag" not in data:
        raise haddock.DeserializeException(f"Expected dict with 'tag' for item, got {data!r}")
    tag = data["tag"]
    cls = _ITEM_REGISTRY.get(tag)  # type: ignore
    if cls is None:
        raise haddock.DeserializeException(f"Unknown item tag: {tag!r}")
    return cls.deserialize(data["payload"])  # type: ignore — delegates to Entity.deserialize()


_register_item(Item)
_register_item(NoItem)


riders: haddock.Riders = [
    SatchelsListRider(),
    SatchelItemsRider(),
    OpenSatchelsEventRider(),
    OpenSatchelItemsEventRider(),
]
chiefs: haddock.Chiefs = []

# Register all events that appear as Action.signal or inside EventSeries
haddock.register_event(OpenSatchelsEvent)
