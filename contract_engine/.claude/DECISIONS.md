# Decisions

## 2025-01-01: DDD layered architecture
Infrastructure depends on application interfaces, not the reverse. Allows swapping the JSON Schema backend or transport without touching domain logic.

## 2025-01-01: Pydantic v2 for domain model
FieldType hierarchy uses `BaseModel` with `extra="forbid"`. Free validation, serialization, deepcopy. `model_rebuild()` handles forward refs in recursive types.

## 2025-01-01: Human-readable seeds hashed to integers
Seeds as strings (`"happyflow"`) for readability in test reports. Hashed to int internally. Batch seeds derived as `{seed}_{index}` for independent replayability.

## 2025-01-01: Overrides applied post-generation
Patch layer on the generated dict, not influencing generation. Keeps generator simple; overrides composable with any schema. Trade-off: can't steer structure, only leaf values.

## 2025-01-01: Refinements as pre-generation contract mutations
Deep-copies contract before mutating — original never touched. Lets test fixtures share a base contract and tighten constraints per test.

## 2025-01-01: Two generation modes (REALISTIC vs FUZZ)
Separate strategy implementations per mode rather than flags. Cleaner extension point; modes can diverge without coupling.

## 2025-01-01: Supported JSON Schema subset intentional
Only features supporting deterministic generation are implemented. `anyOf`, `not`, `if/then/else` excluded — introduce ambiguity that conflicts with seed guarantee.

## 2026-04-24: oneOf refinement via one_of_filter and apply-to-all traversal
Two mechanisms rather than index-based branch selection. `one_of_filter` prunes branches by field/value match — stable against schema reordering, no caller knowledge of option indices needed. Path traversal through `OneOfType` applies to all options containing the field — useful when options share structure. Both operate at refinement time on the deep-copied contract.

## 2026-04-24: Refinement string syntax mirrors override syntax
`key=value` → `{"const": value}`, `key:={...}` → full constraint dict. Consistent API surface for Robot users; no new mini-language to learn. `one_of_filter` is passed via `:=` JSON form.

## 2026-04-24: Root-level oneOf stored as Contract.root_type
A schema of `{"oneOf": [...]}` (no wrapping object) sets `Contract.root_type` rather than synthesizing a named field. Generator special-cases this to produce a flat dict from the selected option. Empty string path `""` addresses root_type in refinements. Keeps field-path semantics clean — no magic field names leaking into user-facing paths.

## 2025-01-01: Robot adapter as thin wrapper
`keywords.py` translates Robot's string-based args to typed Python calls. No logic lives there — keeps the library testable without Robot.
