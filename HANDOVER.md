# Tales of Dragons — Developer Handover

## 1. What We're Building

A **selection-based Viking RPG** in the terminal, built with Python + [Textual](https://textual.textualize.io/). The player navigates a world by clicking text buttons — talking to NPCs, exploring locations, completing quests. No free-text input.

The project has two ambitions running in parallel:

- A **clean game engine** (called Haddock, named after HTTYD characters throughout) with a full MVC split, event sourcing, and save/load.
- **LLM-driven NPCs** via local models (Ollama / Llama 3.1 8B) with isolated per-NPC memory — planned but not yet implemented.

**Stack:** Python 3.10+, Textual (TUI), WSL Ubuntu. No external game libraries. Quest scripts are plain Python async coroutines.

**Repo:** GitHub as `ackvanity`, project at `/home/ackhava/fun/tales-of-dragons` in WSL.

---

## 2. Decisions We've Locked In

### Architecture

**MVC is strict:**
- `clans/` = Controller (game logic, state machines, event handling). No UI code.
- `components/` = View (Textual widgets, RenderChiefs). No game logic.
- `haddock.py` + `librarians/` = Model (engine types, data loading).

**Engine pattern — Hiccup (the engine singleton):**
- State stack: top = active screen. Push/pop via `AppendStateEvent` / `PopStateEvent`.
- Entity registry: `dict[EntityID, Entity]`, keyed by `EntityID(clan, species, name)`.
- Event queue: fully drained before each render pass.
- Riders handle events; Chiefs render commands into widgets. One StateRider per State type, one RenderChief per RenderCommand type.

**Clan naming convention (EntityID):**
- `clan` = Python module name (e.g. `"hofferson"`, `"jorgenson"`)
- `species` = entity type (e.g. `"human"`, `"location"`, `"player"`)
- `name` = unique instance (e.g. `"hiccup"`, `"berk_square"`, `"player"`)
- Player is always `EntityID("jorgenson", "player", "player")`.

**Dragonic — quest scripting:**
- Quests are `async def main()` coroutines in `data/quest/*.py`, loaded via `exec()`.
- They communicate with the engine via `yield`-based syscalls (the coroutine yields a `Syscall` object; the runtime intercepts it, fires engine events, and resumes with the result).
- **Replay model:** every value sent into the coroutine is recorded in `DragonicQuest.data_stream`. On load, the coroutine replays from scratch by feeding it the recorded stream. This means quest scripts MUST be deterministic — no LLM calls inside Dragonic.
- LLM NPC interactions must happen via `add_character_hook()`, which injects a dialogue option and suspends until clicked. The LLM brain sits outside Dragonic entirely.

**Action dataclass (clans/hofferson/__init__.py):**
- Unified type for all player-selectable options across dialogue and navigation.
- `Action(line, signal, condition="True", id="")` where `signal` is a serializable `haddock.Event`.
- Injected module actions use the `extra_character_actions` list protocol.

**Serialization — fully implemented:**
- `Serializable` ABC with `serialize() -> JSONValue`, `deserialize()`, `tag() -> str`.
- `State` and `Entity` add a `[version, payload]` wrapper via `_serialize` / `_deserialize`.
- `Event` also inherits `Serializable` with `{"tag": ..., "payload": ...}` envelope. Non-trivial events override `_serialize_payload()`.
- Three parallel type registries in `haddock.py`: `_STATE_REGISTRY`, `_ENTITY_REGISTRY`, `_EVENT_REGISTRY` — populated via `register_state()`, `register_entity()`, `register_event()` called at the bottom of each clan module.
- `Hiccup.save(path)` / `Hiccup.load(path)` are implemented and walk the state stack + entity dict.
- `DialogueResult` (quest prompt results) and `Action` are both `Serializable`.
- `DragonicQuest._serialize` stores the full `data_stream` with tagged entries.
- `Human._serialize` stores `extra_character_actions` so injected quest hooks survive save/load without coupling to quest replay.

### Data formats (locked)

Characters: `data/character/human/<id>.json` — `id`, `name`, `fullname`, `description`, `interactable`, `menu_lines`, `actions`, `properties.{location, health}`.

Locations: `data/location/<id>.json` — `id`, `name`, `description`, `ambient[]`, `actions[]`.

Connections: `data/location/connections.json` — add here, run `consolidate.py`, never edit location files directly for nav.

Quests: `data/quest/<id>.py` — single `async def main()` coroutine, registered in `main.py`.

Character roster: `data/character/human/humans.json` — plain list of IDs.

### What's intentionally NOT done yet

- `DragonicState` serialization — raises `NotImplementedError` (reserved for future checkpoint system).
- `Satchel._deserialize` is implemented but items use a tag-based registry (`_ITEM_REGISTRY` in `fishlegs.py`). Only `Item` and `NoItem` are registered.
- `eval()` in `librarians/evaluator.py` for event strings in JSON — legacy, works, flagged for replacement.
- LLM NPC memory layer — `NPCMemory` dataclass design is decided but not implemented.

---

## 3. Critical Context a New Chat Would Miss

### Viking theme throughout
The engine uses Viking/HTTYD character names as identifiers. These are intentional and load-bearing — don't rename without understanding the scope:
- `Hiccup` = the engine runner class
- `mail_event()` = queue and dispatch an event
- `roll_call()` = the event handler method on all riders
- `declare_chief()` = register a RenderChief
- `enroll_rider()` = register a rider
- `TeamAssembled` = the boot event fired when the app starts

### The `EventSeries` covariance issue
There's a persistent pyright error in `SendPromptEventRider.roll_call`:
```
Argument of type "list[ReturnDataEvent | PopStateEvent]" cannot be
assigned to parameter "events" of type "list[Event] | None"
```
This is a Python generic covariance limitation. It's pre-existing, benign at runtime, and tracked. Don't try to "fix" it by changing the type — it would require making the list immutable or restructuring the call site.

### `BaseItem.serialize()` is overridden
`BaseItem` overrides `Entity.serialize()` directly (not `_serialize`) to produce `{"tag": ..., "payload": [...]}`. This is intentional — items need their type tag embedded so `_deserialize_item()` in `fishlegs.py` can dispatch to the right subclass. Don't remove this override.

### Module registration order matters
`Hiccup.load()` only works after all clan modules are imported, because `register_state()` / `register_entity()` / `register_event()` are called at module load time. In `main.py`, all clans are imported before the engine runs, so this is guaranteed. Don't move registrations inside functions or lazy-load modules.

### `modules = []` lists in astrid and finn
`astrid.modules` and `finn.modules` hold references to other clan modules that inject extra actions into NPC/location menus. Currently `fishlegs` is appended to both in `main.py`. This is a mutable global — planned for replacement with a proper `register_module()` API but not done yet.

### File reads in `Human`
`Human.__init__` now reads the character JSON once. `Human.line` (the greeting property) still reads the file on each call — this is intentional because greetings are picked randomly per visit and `menu_lines` isn't cached on the entity. The TODO for caching file reads is resolved for `__init__` but the `line` property is left as-is.

### Desktop Commander tool
The conversation uses a `Desktop Commander:start_process` tool that runs bash.exe (WSL) to execute commands, pyflakes, pyright, and git. This is how linting and commits are done. Use this instead of trying to run things on Claude's own filesystem.

---

## 4. What Comes Next

Roughly in priority order:

### Immediate / unblocked
1. **Wire save/load into the UI** — add keyboard shortcut or menu option in `stoick.py` to call `haddock.chieftain.save("saves/slot1.json")` and `load()`. This is the first end-to-end test of the serialization system.
2. **Fix the `eval()` event parser** — `librarians/evaluator.py` uses `eval()` on strings from location/character JSON (e.g. `"finn.LocationTeleportEngineEvent('berk_square')"`) which breaks silently on class renames. Replace with a structured event registry lookup.
3. **Split `snotlout.py`** — it holds Player entity, Dragonic runtime, three quest UI states, all their riders, and all their render commands. Should be at minimum `player.py`, `dragonic.py`, and `quest_states.py`.

### NPC AI (the big feature)
4. **NPC memory layer** — design is decided: `NPCMemory(sentiment: str, memories: list[str], relationship_score: int)` dataclass, serialized separately from engine state, one DB file per NPC. The LLM self-manages via tool calls (`update_sentiment`, `add_memory`, etc.).
5. **LLM NPC brain** — each NPC gets an isolated coroutine/process that receives the player's dialogue choice + NPC memory and returns lines + memory updates. Wired in via `add_character_hook()` so it stays outside Dragonic.
6. **Villain shadow-reasoning** — runs a private `predicted_next_move` / `counter_strategy` profile on every player action. Use a cloud model (Claude Haiku / GPT-4o mini) for this, local 8B for regular NPCs.

### Architecture cleanup (TODO items)
7. Replace `modules = []` lists with `register_module()` API + `Module` dataclass.
8. Rename `data/quest/` to `content/quests/`.
9. Fix `Location.actions` scanning all characters every render — needs event-driven tracking.
10. Type the untyped parameters: `RenderChief.render()` second param, `register_clan()` clan arg, `call_entity()` return type.

---

## 5. Open Questions to Pick Up First

**Q1: How should save slots work?**
Currently `save(path)` / `load(path)` take a raw file path. Do we want named slots, autosave on every state change, or explicit save points in the game world? The Dragonic replay model means save points are natural (save at quest boundaries when `data_stream` is at a stable checkpoint).

**Q2: What happens to a `Prompt` state on load?**
When loading a save where a `Prompt` was the active state, only `script` is restored — `options` is empty. The quest replays its `data_stream` and re-fires `SendPromptEvent`, which repopulates the options. This should work correctly but hasn't been tested end-to-end yet. Needs a manual test once save/load is wired to the UI.

**Q3: Should `DragonicQuest.data_stream` be compressed?**
The stream grows unboundedly — every `None` (auto-advance) and every `DialogueResult` is recorded. For long quests this could get large. The plan is to filter out `None` entries on save (they correspond to auto-advancing syscalls that don't need replay data). Low priority now, but worth deciding before shipping.

**Q4: How do NPC memory DBs interact with `Hiccup.save()`?**
The engine save covers `Human.extra_character_actions` (injected hook actions). But NPC memory (sentiment, episodic memories, relationship score) is meant to be a separate file per NPC, outside the main save. The separation needs to be clearly defined before building the memory layer — otherwise there's a risk of double-saving NPC state.

**Q5: `connections.json` states/transitions are not wired**
The connection file has a full mini state machine (`states`, `steps`, `transitions`) per connection that supports multi-step narrative paths and conditions. `consolidate.py` currently only reads `from`, `to`, and `action`, discarding everything else. Wiring this up would allow rich travel narratives. Decision needed: is this worth the complexity, or should connections stay simple?

---

## Quick Reference

```
haddock.chieftain.save("saves/slot1.json")   # save current state
haddock.chieftain.load("saves/slot1.json")   # restore (clears current state first)

haddock.register_state(MyState)              # must call for every concrete State
haddock.register_entity(MyEntity)            # must call for every concrete Entity
haddock.register_event(MyEvent)              # must call for events used as signals

# Player EntityID is always:
haddock.EntityID("jorgenson", "player", "player")

# Boot sequence:
# main.py imports clans → registrations run → Hiccup() created →
# register_clan() called for each → declare_chief() for each chief →
# initial states/entities seeded → app.run() → on_mount fires TeamAssembled
```

Full developer documentation is in `CONTRIBUTING.md` at the project root.
