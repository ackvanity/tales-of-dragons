import haddock
import json
from clans.hofferson import astrid

class BaseItem(haddock.Entity):
  name: str
  description: str

class Item(BaseItem):
  name: str = "Item"
  description: str = "A generic item. Nobody knows what it is useful for..."


class NoItem(BaseItem):
  name: str = "Empty Slot"
  description: str = "No items here..."

  @property
  def version(self) -> int:
    return 1
  
  def _serialize(self) -> str:
    return ""

  @classmethod
  def _deserialize(cls: type["NoItem"], data: str, version: int) -> "NoItem":
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
  
  def _serialize(self) -> str:
    data = {}
    data["owner"] = self.owner.serialize()
    data["capacity"] = self.capacity
    data["items"] = [item.serialize() for item in self.items]

    return json.dumps(data)
  
  # @classmethod
  # def _deserialize(cls: type["Satchel"], data: str, version: int) -> "Satchel":

class SatchelsList(haddock.State):
  @property
  def version(self) -> int:
    return 1
  
  def _serialize(self) -> str:
    return ""

  @classmethod
  def _deserialize(cls: type["SatchelsList"], data: str, version: int) -> "SatchelsList":
    return cls()

class SatchelItems(haddock.State):
  satchel: haddock.EntityID

  def __init__(self, satchel: haddock.EntityID):
    self.satchel = satchel

  @property
  def version(self) -> int:
    return 1
  
  def _serialize(self) -> str:
    return self.satchel.serialize()

  @classmethod
  def _deserialize(cls: type["SatchelItems"], data: str, version: int) -> "SatchelItems":
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
  
class SatchelsListRenderChief(haddock.RenderChief[SatchelsListRenderCommand]):
  command_type = SatchelsListRenderCommand

  def render(self, command: SatchelsListRenderCommand, application) -> None:
    application.send_satchel_list(command.satchels)

class SatchelItemsRenderChief(haddock.RenderChief[SatchelItemsRenderCommand]):
  command_type = SatchelItemsRenderCommand

  def render(self, command: SatchelItemsRenderCommand, application) -> None:
    application.send_satchel_items({
      "title": command.title,
      "items": command.items
    })

class OpenSatchelsEvent(haddock.EngineEvent):
  pass

class OpenSatchelItemsEvent(haddock.EngineEvent):
  satchel: haddock.EntityID

  def __init__(self, satchel):
    self.satchel = satchel

class OpenSatchelsListAction(astrid.DialogueAction):
  @property
  def line(self):
    return "Check satchel"

  condition: str = "True"
  signal: haddock.Event = OpenSatchelsEvent()

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

extra_character_actions: list[astrid.DialogueAction] = [OpenSatchelsListAction()]
riders: haddock.Riders = [SatchelsListRider(), SatchelItemsRider(), OpenSatchelsEventRider(), OpenSatchelItemsEventRider()]
chiefs: haddock.Chiefs = [SatchelsListRenderChief(), SatchelItemsRenderChief()]