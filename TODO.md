# TODO

## 🔴 Bugs

- [ ] `Satchel._deserialize` is commented out — save/load broken for inventory

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
- [ ] `DragonicQuest.data_stream` checkpoint compression — filter to non-None entries to skip auto-resolved syscalls on replay (very low priority; only relevant if a single quest accumulates tens of thousands of entries across many sessions)
- [ ] LLM-driven NPCs cannot run inside Dragonic — LLM calls are non-deterministic and would break replay. Keep LLM NPC logic entirely outside Dragonic; use `AddCharacterHookSyscall` as the bridge when a quest needs to trigger an NPC interaction
