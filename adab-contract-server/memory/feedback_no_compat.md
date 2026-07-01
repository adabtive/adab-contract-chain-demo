---
name: No backwards compatibility shims
description: Don't add coercion/shims for old config formats — just update the handful of files directly
type: feedback
---

Don't add backwards compatibility shims (e.g. field_validator string coercion) when the existing configs are few and easy to update manually.

**Why:** codebase is small, only ~3 YAML configs exist, all in one demo project. Coercion adds complexity for no real benefit at this stage.

**How to apply:** when changing a config schema, just migrate existing files directly instead of writing fallback parsing logic.
