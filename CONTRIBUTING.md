# Tales of Dragons — Developer Guide

## Table of Contents

1. [Project overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Engine core — `haddock.py`](#3-engine-core--haddockpy)
4. [Clans — Controllers](#4-clans--controllers)
5. [Librarians — Model / data layer](#5-librarians--model--data-layer)
6. [Components — View layer](#6-components--view-layer)
7. [Dragonic — Quest scripting runtime](#7-dragonic--quest-scripting-runtime)
8. [Serialization interface](#8-serialization-interface)
9. [Data formats](#9-data-formats)
10. [Adding new content](#10-adding-new-content)

---

## 1. Project overview

Tales of Dragons is a selection-based Viking RPG built in Python using [Textual](https://textual.textualize.io/) for the terminal UI. Game logic is driven by an event-sourced engine (`haddock.py`), with quest scripting handled by a coroutine-based DSL called Dragonic.

The project is structured as MVC:

| Layer | Location | Responsibility |
|---|---|---|
| Model | `haddock.py`, `librarians/` | Engine types, data loading |
| Controller | `clans/` | Game logic, state machines, event handling |
| View | `components/`, `stoick.py` | Textual widgets, rendering |

---

## 2. Architecture

### Module map

```
haddock.py              Engine core: State, Entity, Event, Hiccup (engine runner)
stoick.py               Textual Application shell (View entry point)
main.py                 Bootstrap: wires clans, chiefs, initial state

clans/
  hofferson/
    __init__.py         Shared Action dataclass for the hofferson module
    astrid.py           NPC / dialogue system (Human, Talking state)
    finn.py             Location / navigation system (Location, Wandering state)
  ingerman/
    fishlegs.py         Inventory system (Satchel, items)
  jorgenson/
    snotlout.py         Player entity, Dragonic quest runtime, UI states

librarians/
  core.py               Data file loader (JSON + Python scripts)
  evaluator.py          eval()-based event string parser (legacy, to be replaced)
  hofferson/
    __init__.py         get_humans() — loads character roster from data/
    astrid.py           CharacterData parser
    finn.py             LocationData parser

components/
  base.py               EventEmitButton (fires haddock events on press)
  hofferson/
    __init__.py         Story, Prompt, Dialogue, Paragraph Textual widgets
    astrid.py           Character widget + TalkingRenderChief
    finn.py             Location widget + WanderingRenderChief
  ingerman/
    fishlegs.py         SatchelList, SatchelItems widgets + their chiefs
  jorgenson/
    snotlout.py         Prompt, Dialogue, Story render chiefs

dragonic/
  base.py               Syscall base classes, Proxy, attribute path types
  core.py               world proxy object (used in quest scripts)
  interactions.py       Syscall helpers: send_dialogue, send_prompt, etc.

data/
  character/human/      JSON character definitions
  location/             JSON location definitions + connections.json
  items/                JSON item definitions
  quest/                Python quest scripts (Dragonic coroutines)
```

### Event flow

Every player action produces a `haddock.Event`. The engine (`Hiccup`) dispatches it:

1. **EngineEvents** are handled by registered `EventRider`s or by `Hiccup` itself (state push/pop).
2. **Non-engine events** are broadcast to all `EntityRider`s (one per entity type), then to the active `StateRider`.
3. After all events are drained, `Hiccup` calls `render()` on the current top-of-stack `State` via its `StateRider`, which produces a `RenderCommand`.
4. The matching `RenderChief` receives the command and mounts Textual widgets.

```
Player presses button
  -> EventEmitButton fires haddock.Event
    -> Hiccup.mail_event()
      -> StateRider.roll_call() / EntityRider.roll_call()
        -> may mail_event() more events (state changes, etc.)
      -> StateRider.render() -> RenderCommand
        -> RenderChief.render() -> Textual widget mounted
```

---

## 3. Engine core — `haddock.py`

### Key types

**`State`** — A screen or mode the game is in. States are stacked; the top of the stack is active. Extend `State` to create new screens.

```python
class MyState(haddock.State):
    @staticmethod
    def tag() -> str: return "mymodule.MyState"

    @property
    def version(self) -> int: return 1

    def _serialize(self) -> haddock.JSONValue: ...
    @classmethod
    def _deserialize(cls, data: haddock.JSONValue, version: int) -> "MyState": ...
```

**`Entity`** — A persistent game object (NPC, location, player, satchel). Lives in `Hiccup.entities` keyed by `EntityID`. Extend `Entity` to create new object types.

**`EntityID`** — A frozen dataclass `(clan: str, species: str, name: str)`. Used as the dict key for all entities. Convention: `clan` matches the Python module clan name, `species` is the entity type, `name` is the unique identifier.

```python
# Examples
EntityID("hofferson", "human", "hiccup")
EntityID("hofferson", "location", "berk_square")
EntityID("jorgenson", "player", "player")
EntityID("ingerman", "satchel", "1")
```

**`Event`** / **`EngineEvent`** — Plain events are broadcast to riders. `EngineEvent`s are intercepted by `Hiccup` or `EventRider`s before reaching state/entity riders.

**`Hiccup`** — The engine singleton, accessed via `haddock.chieftain`. Key methods:

| Method | Purpose |
|---|---|
| `mail_event(event)` | Queue and dispatch an event |
| `call_entity(id, default?)` | Fetch entity by ID, optionally creating it |
| `call_entities(clan?, species?, name?)` | Filter entities by partial ID |
| `register_clan(clan_module)` | Register all riders/chiefs from a clan |
| `declare_chief(chief)` | Register a render chief |

**`Action`** (in `clans/hofferson/__init__.py`) — A dataclass representing a selectable option presented to the player:

```python
@dataclass
class Action:
    line: str           # Button label shown to the player
    signal: Event       # Event fired when the player selects this action
    condition: str = "True"   # Future: evaluated to determine visibility
    id: str = ""        # Used by quest hooks to identify removable actions
```

---

## 4. Clans — Controllers

Each clan is a Python module that registers `riders` and `chiefs` lists with the engine. Clans own the game logic for their domain.

### Rider types

**`StateRider[S]`** — Handles events while state `S` is active, and renders it.
- `roll_call(state, event)` — react to events
- `render(state) -> RenderCommand` — produce output for the view

**`EntityRider[E]`** — Handles events addressed to entities of type `E`.
- `roll_call(entity, event)` — react to events (all active entities of this type receive the call)

**`EventRider[V]`** — Handles a specific `EngineEvent` type globally.
- `roll_call(event)` — handle the engine event

### `clans/hofferson/astrid.py` — NPC dialogue

Key classes:
- `Human` — Entity representing an NPC. Holds `extra_character_actions: list[Action]` for quest-injected dialogue options.
- `Talking` — State for when the player is speaking to an NPC.
- `HumanInteractEngineEvent(to: str)` — Push a `Talking` state for a given NPC ID.
- `AddDialogueEvent(character, line, event, id)` — Inject a dialogue option into an NPC.
- `RemoveDialogueEvent(character, id)` — Remove a previously injected dialogue option.

### `clans/hofferson/finn.py` — Navigation

Key classes:
- `Location` — Entity representing a map location. Holds `extra_location_actions: list[Action]`.
- `Wandering` — State for when the player is exploring a location.
- `LocationTeleportEngineEvent(to: str)` — Push a `Wandering` state for a given location ID.

### `clans/ingerman/fishlegs.py` — Inventory

Key classes:
- `Satchel` — Entity holding a list of `BaseItem`s with a capacity.
- `SatchelsList` / `SatchelItems` — UI states for browsing inventory.
- `OpenSatchelsEvent` / `OpenSatchelItemsEvent` — Open inventory screens.

Module-level `extra_character_actions` exposes a "Check satchel" action injected into all NPC menus.

### `clans/jorgenson/snotlout.py` — Player and Dragonic runtime

Key classes:
- `Player` — Entity holding player name and health.
- `DragonicQuest` — Entity wrapping a running quest coroutine. Drives the Dragonic scripting runtime.
- `Prompt` / `Dialogue` / `Story` — Transient states used by Dragonic to display content and collect player choices.

---

## 5. Librarians — Model / data layer

### `librarians/core.py`

```python
def get_data(path: str | Iterable[str], ext: str = "json", parse: bool = True)
```

Loads a file from `data/`. `path` can be a string like `"character/human/hiccup"` or a list `["quest", "rescue_hiccup_toothless"]`. Returns parsed JSON by default, or raw string when `parse=False`.

### `librarians/hofferson/astrid.py`

Parses `CharacterData` from a character JSON dict. See [Data formats -> Characters](#characters).

### `librarians/hofferson/finn.py`

Parses `LocationData` from a location JSON dict. See [Data formats -> Locations](#locations).

### `librarians/evaluator.py`

Parses event strings (e.g. `"finn.LocationTeleportEngineEvent('berk_square')"`) using `eval()` against a controlled scope containing `astrid`, `finn`, and `fishlegs`. **This is a temporary solution** — see TODO for planned replacement with a structured event registry.

---

## 6. Components — View layer

Components are Textual widgets. They receive `RenderCommand` objects from the engine and mount themselves into the `Story` container in `stoick.py`.

### `stoick.py` — `TextualApplication`

The Textual `App` shell. Key methods:
- `get_mount_point()` — the root `#application` container
- `get_story() -> Story | None` — the active `Story` widget if present
- `ensure_singleton(klass)` — ensure exactly one widget of `klass` is mounted
- `clear_history()` — remove all children from the mount point

### Render chiefs

Each `RenderChief[C]` receives a `RenderCommand` of type `C` and mounts widgets asynchronously via `asyncio.create_task`. Chiefs live in `components/` alongside the widgets they render.

| Chief | Command | File |
|---|---|---|
| `TalkingRenderChief` | `TalkingRenderCommand` | `components/hofferson/astrid.py` |
| `WanderingRenderChief` | `WanderingRenderCommand` | `components/hofferson/finn.py` |
| `SatchelsListRenderChief` | `SatchelsListRenderCommand` | `components/ingerman/fishlegs.py` |
| `SatchelItemsRenderChief` | `SatchelItemsRenderCommand` | `components/ingerman/fishlegs.py` |
| `PromptRenderChief` | `PromptRenderCommand` | `components/jorgenson/snotlout.py` |
| `DialogueRenderChief` | `DialogueRenderCommand` | `components/jorgenson/snotlout.py` |
| `StoryRenderChief` | `StoryRenderCommand` | `components/jorgenson/snotlout.py` |

Chiefs are registered in `main.py` via `haddock.chieftain.declare_chief(...)`.

---

## 7. Dragonic — Quest scripting runtime

Dragonic is a coroutine-based scripting system for writing quest scripts in plain Python. Quest scripts live in `data/quest/` and are loaded and `exec()`'d at runtime by `DragonicQuest`.

### Writing a quest script

A quest script is a Python file with a single `async def main()` coroutine. Import helpers from `dragonic.interactions`:

```python
from dragonic.interactions import (
    send_dialogue,       # show a character saying a line, auto-advance
    send_story,          # show a narration paragraph, auto-advance
    send_prompt,         # show player choices, returns DialogueResult
    send_pause,          # show a single "Continue" button
    add_character_hook,  # inject a dialogue option into an NPC
)
from dragonic.core import world  # proxy for reading game state

async def main():
    await add_character_hook("hiccup", "Hey Hiccup!")
    await send_dialogue("Hiccup", "Oh hey! Want to come flying?")
    option = await send_prompt(["Yes!", "No thanks."])
    if option.index == 0:
        name = await world.player.name
        await send_story(f"The two of you soar into the clouds.")
        await send_dialogue("Hiccup", f"Great flying, {name}!")
```

### API reference

**`send_dialogue(speaker: str, line: str)`**
Displays a dialogue line attributed to `speaker`. Auto-advances after rendering.

**`send_story(text: str)`**
Displays a narration paragraph with no speaker. Auto-advances after rendering.

**`send_prompt(options: list[str]) -> DialogueResult`**
Displays player choices. Suspends until one is selected. Returns:
- `.index: int` — zero-based index of chosen option
- `.text: str` — label of chosen option

**`send_pause()`**
Displays a single "Continue" button. Use after story beats that need breathing room.

**`add_character_hook(character_id: str, line: str)`**
Injects a dialogue option into the NPC with the given ID. Suspends until the player clicks it. The option self-removes when clicked.

**`world.player.name`** / **`world.player.health`**
`world` is a lazy proxy. `await world.player.name` reads the player entity's `name` field at runtime.

### Important constraints

- **Quest scripts must be deterministic.** The same inputs must always produce the same execution path, because the quest is replayed from scratch on load using the recorded `data_stream`.
- **Do not make LLM calls inside quest scripts.** LLMs are non-deterministic and break replay. Use `add_character_hook` to hand off to the NPC brain system instead.
- **Do not use `send_pause` before a `send_prompt`.** The prompt already acts as a pause point.

---

## 8. Serialization interface

All persistent game objects implement `Serializable` (via `State` or `Entity`). Serialization is currently **disabled** (abstract methods commented out) to allow testing during refactoring.

### Contract

```python
class Serializable(ABC):
    def serialize(self) -> JSONValue: ...
    @classmethod
    def deserialize(cls, data: JSONValue) -> Self: ...
    @staticmethod
    def tag() -> str: ...    # globally unique string key for type registry
```

`State` and `Entity` wrap `_serialize()` output as `[version, payload]`. Subclasses implement `_serialize` and `_deserialize` only.

### Implementing serialization

```python
class MyState(haddock.State):
    @staticmethod
    def tag() -> str:
        return "mymodule.MyState"       # globally unique

    @property
    def version(self) -> int:
        return 1                        # increment when format changes

    def _serialize(self) -> haddock.JSONValue:
        return {"field": self.field}    # plain Python dict/list/str/int only

    @classmethod
    def _deserialize(cls, data: haddock.JSONValue, version: int) -> "MyState":
        if version == 1:
            if not isinstance(data, dict):
                raise haddock.DeserializeException(f"Expected dict, got {data!r}")
            return cls(field=data["field"])
        raise haddock.DeserializeVersionUnsupportedException()
```

### `JSONValue` type

`str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]`

Return only JSON-compatible Python types from `_serialize`. Do not call `json.dumps` — return native Python objects. Never return custom class instances.

---

## 9. Data formats

All data files live under `data/`. JSON files are loaded via `librarians/core.get_data()`.

### Characters

**Path:** `data/character/human/<id>.json`

```json
{
  "id": "hiccup",
  "name": "Hiccup",
  "fullname": "Hiccup Horrendous Haddock III",
  "description": "Full prose description of the character.",
  "interactable": true,
  "menu_lines": [
    "So, what should we do today?",
    "Got anything new?"
  ],
  "actions": [],
  "properties": {
    "location": "berk_square",
    "health": 100
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique; must match the filename without `.json` |
| `name` | string | yes | Short display name shown in dialogue |
| `fullname` | string | yes | Full name for prose and descriptions |
| `description` | string | yes | Character bio; not currently shown in-game |
| `interactable` | bool | yes | If false, character cannot be spoken to |
| `menu_lines` | string[] | yes | Greeting lines; one chosen at random per visit |
| `actions` | ActionData[] | yes | Static dialogue options; usually `[]` — use quests for dynamic options |
| `properties.location` | string | yes | Starting location ID |
| `properties.health` | int | no | Default: 100 |

**ActionData** (inside `actions` array — legacy format, to be replaced):

```json
{ "line": "Button label", "event": "finn.LocationTeleportEngineEvent('berk_square')" }
```

**Character roster:** `data/character/human/humans.json`

Plain JSON array of all character IDs the engine should load:

```json
["hiccup", "astrid"]
```

---

### Locations

**Path:** `data/location/<id>.json`

```json
{
  "id": "berk_square",
  "name": "The Village Square",
  "description": "Short prose description.",
  "ambient": [
    "Children shriek with laughter as a sheep dashes between stalls...",
    "An alternate ambient line chosen at random."
  ],
  "actions": [
    {
      "line": "I could follow the open lane leading downhill.",
      "event": "finn.LocationTeleportEngineEvent('berk_stables')"
    }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique; must match filename without `.json` |
| `name` | string | yes | Display name |
| `description` | string | yes | Prose description; not shown directly in-game |
| `ambient` | string[] | yes | Scene-setting narration; one chosen at random |
| `actions` | ActionData[] | yes | Navigation and interaction options |

~~**Do not add connections directly to location files.** Define them in `connections.json` and run `consolidate.py`.~~

**Do not use `consolidate.py`**. It is a legacy migration script and will be removed in a future release.

**DO define connections using the "actions" field**. To add flavor text, emit events. In the future, a built-in solution will be given.

---

### Quest scripts

**Path:** `data/quest/<id>.py`

A Python file containing `async def main()`. The filename without `.py` is the quest ID.

```python
from dragonic.interactions import send_dialogue, send_prompt, send_story, add_character_hook
from dragonic.core import world

async def main():
    await add_character_hook("hiccup", "Hey Hiccup, is that a new tailfin?")
    await send_dialogue("Hiccup", "If you put it that way... yes.")
    option = await send_prompt(["Can I come along?", "Maybe later."])
    if option.index == 0:
        await send_story("The two of you soar into the open sky.")
```

Register in `main.py`:

```python
haddock.chieftain.entities[
    haddock.EntityID("jorgenson", "quest", "<id>")
] = snotlout.DragonicQuest("<id>")
```

The quest starts automatically on game boot if it has not been started before. It resumes whenever a `ReturnDataEvent` arrives addressed to its ID (which happens automatically after `send_dialogue`, `send_story`, and `send_prompt` complete). You should not need to handle events and communication with the game engine in any manner, including by handling a `ReturnDataEvent`, unless you are working with custom bindings to the game engine, mostly used for stateful operations. In that case, you will most likely need to extend `jorgenson/snotlout.py` to handle or delegate the operation correctly.

---

### Items

**Path:** `data/items/<id>.json`

Item JSON format is not yet standardized. The `BaseItem` / `Item` / `NoItem` hierarchy in `fishlegs.py` defines the runtime type. Item loading from JSON is not yet implemented.

---

## 10. Adding new content

### Add a new NPC

1. Create `data/character/human/<id>.json` with the character schema.
2. Add the ID to `data/character/human/humans.json`.
3. Set `"properties": { "location": "<location_id>" }` to place them.

No code changes required. The NPC will appear as an interactable option in their starting location.

### Add a new location

1. Create `data/location/<id>.json` with the location schema.
2. Add connections from existing locations in `data/location/connections.json`.
3. Run `python consolidate.py` from the project root.

### Add a new quest

1. Create `data/quest/<id>.py` with `async def main()`.
2. Register it in `main.py`:
   ```python
   haddock.chieftain.entities[
       haddock.EntityID("jorgenson", "quest", "<id>")
   ] = snotlout.DragonicQuest("<id>")
   ```

### Add a new clan (game system)

1. Create `clans/<clanname>/<module>.py` with `Entity`/`State` subclasses, `Rider`s, and `RenderCommand` types.
2. Create `components/<clanname>/<module>.py` with matching `RenderChief`s and Textual widgets.
3. Register in `main.py`:
   ```python
   from clans.<clanname> import <module>
   from components.<clanname>.<module> import MyRenderChief
   haddock.chieftain.register_clan(<module>)
   haddock.chieftain.declare_chief(MyRenderChief())
   ```


**TODO: Write about the TCSS system**
**The color palette is at https://coolors.co/7c6c77-e59f71-d00000-0c1618-03254e **