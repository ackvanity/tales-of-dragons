import haddock
from clans.hofferson import Action

class BaseItem(haddock.Entity):
  name: str
  description: str

  def serialize(self) -> haddock.JSONValue:
    raise NotImplementedError

class Item(BaseItem):
  name: str = "Item"
  description: str = "A generic item. Nobody knows what it is useful for..."


class NoItem(BaseItem):
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

class Satchel(haddock.Entity):
  owner: haddock.EntityID
  items: list[BaseItem]
  capacity: int = 10

  def __init__(self, items: list[BaseItem], capacity: int, owner: haddock.EntityID):
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
  
  # @classmethod
  # def _deserialize(cls: type["Satchel"], data: str, version: int) -> "Satchel":

class SatchelsList(haddock.State):
  @property
  def version(self) -> int:
    return 1
  
  def _serialize(self) -> haddock.JSONValue:
    return ""

  @classmethod
  def _deserialize(cls: type["SatchelsList"], data: haddock.JSONValue, version: int) -> "SatchelsList":
    return cls()

class SatchelItems(haddock.State):
  satchel: haddock.EntityID

  def __init__(self, satchel: haddock.EntityID):
    self.satchel = satchel

  @property
  def version(self) -> int:
    return 1
  
  def _serialize(self) -> haddock.JSONValue:
    return self.satchel.serialize()

  @classmethod
  def _deserialize(cls: type["SatchelItems"], data: haddock.JSONValue, version: int) -> "SatchelItems":
    if version == 1:
      return cls(haddock.EntityID.deserialize(data))
    else:
      raise haddock.DeserializeVersionUnsupportedException

class SatchelsListRenderCommand(haddock.RenderCommand):
  satchels: list[tuple[str, haddock.Event]]

  def __init__(self, satchels: list[tuple[str, haddock.EntityID]]):
    self.satchels = [(name, OpenSatchelItemsEvent(get_satchel(owner))) for name, owner in satchels] # type: ignore

class SatchelItemsRenderCommand(haddock.RenderCommand):
  title: str
  items: list[BaseItem]

  def __init__(self, title: str, items: list[BaseItem]):
    self.title = title
    self.items = items

class SatchelsListRider(haddock.StateRider[SatchelsList]):
  state_type = SatchelsList
  
  def roll_call(self, state: SatchelsList, event: haddock.Event) -> None:
    if isinstance(event, CloseSatchelsListEvent):
      haddock.chieftain.mail_event(haddock.PopStateEvent())

  def render(self, state: SatchelsList) -> haddock.RenderCommand:
        return SatchelsListRenderCommand([("My satchel", haddock.EntityID("haddock", "player", "player"))])

class SatchelItemsRider(haddock.StateRider[SatchelItems]):
  state_type = SatchelItems

  def roll_call(self, state: SatchelItems, event: haddock.Event) -> None:
    if isinstance(event, CloseSatchelItemsEvent):
      haddock.chieftain.mail_event(haddock.PopStateEvent())

  def render(self, state: SatchelItems) -> haddock.RenderCommand:
    def no_default():
      raise Exception("Satchel was a ghost?")
    
    satchel: Satchel = haddock.chieftain.call_entity(state.satchel, no_default) # type: ignore

    return SatchelItemsRenderCommand(f"Satchel ({satchel.capacity} items)", satchel.items + [NoItem() for _ in range(satchel.capacity - len(satchel.items))])
  
class OpenSatchelsEvent(haddock.EngineEvent):
  pass

class OpenSatchelItemsEvent(haddock.EngineEvent):
  satchel: haddock.EntityID

  def __init__(self, satchel):
    self.satchel = satchel

open_satchels_action = Action(
  line="Check satchel",
  signal=OpenSatchelsEvent(),
)

class CloseSatchelsListEvent(haddock.Event):
  pass

class CloseSatchelItemsEvent(haddock.Event):
  pass

class OpenSatchelsEventRider(haddock.EventRider[OpenSatchelsEvent]):
  event_type = OpenSatchelsEvent

  def roll_call(self, event: OpenSatchelsEvent) -> None:
    haddock.chieftain.mail_event(haddock.AppendStateEvent(SatchelsList()))

class OpenSatchelItemsEventRider(haddock.EventRider[OpenSatchelItemsEvent]):
  event_type = OpenSatchelItemsEvent

  def roll_call(self, event: OpenSatchelItemsEvent) -> None:
    haddock.chieftain.mail_event(haddock.AppendStateEvent(SatchelItems(event.satchel)))

def get_satchel(owner: haddock.EntityID):
  satchels = haddock.chieftain.call_entities('ingerman', 'satchel', None)

  for id, satchel in satchels:
    if satchel.owner == owner:
      return id
  
  raise Exception("No satchel?")

extra_character_actions: list[Action] = [open_satchels_action]
riders: haddock.Riders = [SatchelsListRider(), SatchelItemsRider(), OpenSatchelsEventRider(), OpenSatchelItemsEventRider()]
chiefs: haddock.Chiefs = []