# TODO

## 🔴 Bugs

- [ ] `Satchel._deserialize` is commented out — save/load broken for inventory

## 🟡 Architecture

- [ ] Split `snotlout.py` — currently holds Player entity, Dragonic runtime, quest states, all riders/chiefs (at least 4 responsibilities)
- [ ] Replace `eval()` in `librarians/evaluator.py` and `consolidate.py` with an event registry — class renames silently break all location JSON files
- [ ] Implement `tag()` on all concrete `State` and `Entity` subclasses to unblock instantiation: `Talking`, `Wandering`, `NoItem`, `Satchel`, `SatchelsList`, `SatchelItems`, `Prompt`, `Dialogue`, `Story`, `Player`, `DragonicQuest`
- [ ] Build save/load orchestration on `Hiccup` — no code currently walks engine state and serializes it
- [ ] Replace mutable module-level `modules = []` lists in `astrid` and `finn` with explicit `register_module()` API + `Module` dataclass or ABC
- [ ] Rename `data/quest/` to `content/quests/` — quest scripts are executable Python, not static data
- [ ] `Location.actions` scans all characters on every render — should use event-driven location tracking instead

## 🔧 Chores

- [ ] `RenderChief.render()` second parameter typed as bare `object` / untyped throughout — should be `TextualApplication` now that chiefs live in the View layer
- [ ] `StateRider.render()` and `roll_call()` use untyped `Event` rather than the specific subtype — consider bounded generics or overloads where the event type is known
- [ ] `Hiccup.register_clan()` takes untyped `clan` — should accept a typed protocol/dataclass with `riders` and `chiefs` attributes
- [ ] `Hiccup.call_entity()` return type is untyped — generic overload with `Type[E]` hint on the `default` param would let callers skip the `# type: ignore`
- [ ] `DragonicQuest.__init__` default arg `data_stream=[]` is a mutable default — replace with `data_stream=None` and assign in body

## 📛 Naming inconsistencies

- [ ] `SatchelsList` / `SatchelsListRider` / `SatchelsListRenderCommand` — plural possessive ("Satchels") is inconsistent with `SatchelItems` / `SatchelItemsRider`. Should be `SatchelList` throughout (matches the component widget name already)
- [ ] `BaseAddDialogueEvent` — the "Base" prefix is confusing; it's not an ABC, it's the non-engine variant of `AddDialogueEvent`. Rename to `AddDialogueNonEngineEvent` or restructure to use a single event type
- [ ] `HumanInteractEvent` / `HumanInteractEngineEvent` — the "Base" mixin `HumanInteractEventBase` uses a different naming pattern from `LocationTeleportEventBase`. One uses `EventBase`, the other is identical. Consistent pattern needed
- [ ] `extra_lines` on `Human` — stores injected `Action` objects but is named `lines` implying strings. Rename to `extra_actions` to match `Location.extra_actions`
- [ ] `extra_character_actions` (in modules/fishlegs) vs `extra_actions` (on `Location`) — the module injection attribute is named differently from the entity storage attribute. Pick one convention: `extra_actions` everywhere
- [ ] `WanderingRenderCommand.line` — field named `line` holds the ambient description string. Should be `ambient` to match what `Location.ambient` produces and what the render dict key already calls it
- [ ] `roll_call` — the event handler method on all riders. Evocative name but not obvious to new readers; worth a comment or rename to `handle_event` / `on_event` when the API stabilises
- [ ] `mail_event` / `TeamAssembled` / `declare_chief` / `enroll_rider` — all thematic Viking names on `Hiccup`. Fine as-is, but if the codebase ever needs to separate the theme from the API, these would all need updating together
- [ ] `clans/ingerman/fishlegs.py` exports `open_satchels_action` as a module-level singleton — naming convention for module-level action singletons is not yet established (everything else uses class names). Consider a consistent pattern e.g. `OPEN_SATCHELS_ACTION` (SCREAMING_SNAKE for constants) or wrap in a proper `module` object per the planned `register_module()` refactor

## 🟢 Enhancements

- [ ] Cache file reads in `Human.__init__` — currently calls `parse_character_data(core.get_data(...))` three separate times
- [ ] NPC memory layer — `NPCMemory` dataclass (sentiment, episodic list, relationship score) saved separately from engine state
- [ ] Villain shadow-reasoning system — player profiling + private "predicted next move" updated after every player action
- [ ] `DragonicQuest.data_stream` checkpoint compression — filter to non-None entries to skip auto-resolved syscalls on replay (very low priority; only relevant if a single quest accumulates tens of thousands of entries across many sessions)
- [ ] LLM-driven NPCs cannot run inside Dragonic — LLM calls are non-deterministic and would break replay. Keep LLM NPC logic entirely outside Dragonic; use `AddCharacterHookSyscall` as the bridge when a quest needs to trigger an NPC interaction
