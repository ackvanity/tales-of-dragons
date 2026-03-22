# TODO

## 🔴 Bugs

- [ ] `Satchel._deserialize` is commented out — save/load broken for inventory
- [ ] `DragonicQuest.data_stream` grows forever, never pruned — replay cost increases unbounded
- [ ] `stoick.py` async callback race: `group.children[0]` accessed before mount completes in `send_location` / `send_character`

## 🟡 Architecture

- [ ] Split `snotlout.py` — currently holds Player entity, Dragonic runtime, quest states, all riders/chiefs (at least 4 responsibilities)
- [ ] Replace `eval()` in `librarians/evaluator.py` and `consolidate.py` with an event registry — class renames silently break all location JSON files
- [ ] Make `Entity` extend `Serializable` — currently reimplements the interface manually without inheriting it
- [ ] Add `tag()` implementations to all concrete `Entity` and `State` subclasses — required for save/load type registry
- [ ] Build save/load orchestration on `Hiccup` — no code currently walks engine state and serializes it
- [ ] `stoick.py` knows about `fishlegs` inventory types directly — breaks MVC boundary; `Application` should accept a generic `RenderCommand` instead of named per-feature methods
- [ ] Replace mutable module-level `modules = []` lists in `astrid` and `finn` with explicit `register_module()` API + `Module` dataclass or ABC
- [ ] Rename `data/quest/` to `content/quests/` — quest scripts are executable Python, not static data
- [ ] `Location.actions` scans all characters on every render — should use event-driven location tracking instead

## 🟢 Enhancements

- [ ] Cache file reads in `Human.__init__` — currently calls `parse_character_data(core.get_data(...))` three separate times
- [ ] NPC memory layer — `NPCMemory` dataclass (sentiment, episodic list, relationship score) saved separately from engine state
- [ ] Villain shadow-reasoning system — player profiling + private "predicted next move" updated after every player action
- [ ] `JsonValue` recursive type alias — enforce JSON-compliant return types on serialize methods

## ✅ Done

- [x] Mutable class-level defaults on `Hiccup` (`states`, `entities`, `event_queue`, etc.) — moved to `__init__`
- [x] `TeamAssmebled` typo — fixed to `TeamAssembled` across `haddock.py`, `stoick.py`, `snotlout.py`
- [x] `entites` typo in `call_entities` — fixed to `entities`
- [x] `"Emply Slot"` typo in `fishlegs.py` — fixed to `"Empty Slot"`
- [x] `self.ke = key` bug in `dragonic/base.py` `Item.__init__` — fixed to `self.key`
- [x] `self.pathj` bug in `dragonic/core.py` `Proxy.set()` — fixed to `self._path`
- [x] Private email in git history — scrubbed and force-pushed
