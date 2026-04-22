# Schema

Canonical frontmatter schemas for every file in `cto-os-data`. Single source of truth. The data-repo pre-commit hook validates writes against this file.

When this file changes in a way that affects existing state, bump the relevant type's version and ship a migration (`scripts/migrate_{type}_v{N}_to_v{N+1}.py`). See [docs/SKILL_REPO.md → Schema evolution](../docs/SKILL_REPO.md#schema-evolution).

---

## Conventions

- **Frontmatter** is YAML between `---` markers at the top of each `.md` file.
- **`type`** is the discriminator — it selects which schema applies to the file.
- **Type names** are `lowercase-kebab-case`. A leading underscore (`_module`) marks meta files that hold module-level state rather than user content.
- **Required fields** must be present and non-null. **Optional fields** may be absent; the value falls back to the default documented per field.
- **Sensitivity** defaults to `standard`. Files or modules marked `sensitivity: high` are excluded from `scan` results unless the caller explicitly includes them.
- **Module extensions:** each module defines one or more per-type schemas below. Those schemas extend the baseline; they may add required and optional fields but must not contradict the baseline.

---

## Baseline (every frontmatter)

Applies to every `.md` file in `cto-os-data`, regardless of type.

```yaml
type: string          # required; lowercase-kebab-case; discriminator
slug: string          # required; unique within this module's files of the same type; lowercase-kebab-case
updated: date         # required; ISO 8601 (YYYY-MM-DD)
sensitivity: enum     # optional; one of: standard (default), high
```

Notes:
- `slug` uniqueness is scoped per-module per-type. Modules can't collide with each other regardless — they live in separate directories — so no global uniqueness requirement exists.
- `updated` bumps on every write. Modules are responsible for setting it correctly in their write path.
- `sensitivity` on a state file overrides the module-level default (see `_module.md` below).

---

## `_module` — module activation record

Lives at `cto-os-data/modules/{slug}/_module.md`. One per module. Tracks whether the module is active, when it was activated, and the schema version currently in use.

```yaml
type: _module                   # required; literal string "_module"
slug: string                    # required; matches the module directory name
module: string                  # required; same value as slug (explicit for readability)
updated: date                   # required
schema_version: int             # required; the canonical version for this module's types
active: bool                    # required
activated_at: date              # required if ever activated; null before first activation
deactivated_at: date            # required; null if currently active
sensitivity: enum               # optional; module-wide default inherited by state files unless overridden
activation_completed: list[int] # optional; step numbers of the module's activation flow that have finished
```

**Rules:**
- When `active` flips to `true`, set `activated_at` and clear `deactivated_at` (set to `null`).
- When `active` flips to `false`, set `deactivated_at`; leave `activated_at` untouched (history).
- `schema_version` is bumped only by a migration script, never by hand.
- `sensitivity: high` on `_module.md` applies defense-in-depth to every file in this module's `state/` unless a specific file sets its own value.
- Scan excludes `active: false` modules by default; callers must opt in to see inactive state.
- **`activation_completed`** is the authoritative resumption signal. File-presence is a useful secondary check (most steps write a concrete artifact), but a step is "done" only when its number is in this list. This handles edge cases cleanly: steps with branching answers captured into a shared file, multiple steps that target the same file, or steps with only behavioral effects. When omitted or empty, activation hasn't started.

**Current version:** 1.

---

## Per-module types

Each module introduces one or more types. Their schemas are defined under a `## <type>` heading, following the same shape as `_module` above.

When a module adds a type:

1. Add a `## <type>` section with the YAML block.
2. Declare required and optional fields; don't restate baseline fields.
3. Document any invariants (e.g., "one file per `person-slug` per `date`").
4. Add the type to the version table below with version `1`.
5. Set the owning module's `schema_version` in `_module.md` accordingly.

---

## `altitude`

The user's role altitude. One per user; owned by `personal-os`.

```yaml
level: enum        # required; one of: director, vp, svp, c-level
context: string    # required; one-line descriptor of the role's shape
```

Invariant: exactly one file per user at `state/altitude.md` with `slug: current`.

**Current version:** 1.

---

## `goal-horizon`

Personal goals at one of three horizons: annual, quarterly, or weekly. Owned by `personal-os`. One file per horizon; each updates on its own cadence without touching the others.

```yaml
horizon: enum        # required; one of: annual, quarterly, weekly. Same value as slug — explicit discriminator for scan.
period: string       # required; "2026" for annual, "2026-Q2" for quarterly, "2026-W16" for weekly
items: list[string]  # required; the goals themselves
```

Invariants:
- Files live at `state/goals/{annual|quarterly|weekly}.md`.
- `slug` equals `horizon`.
- Each file holds its own reverse-chronological snapshots under `## History` in the body.

**Current version:** 1.

---

## `show-up`

Declarative statement of how the user wants to show up as a leader. Owned by `personal-os`.

No required fields beyond baseline. Body carries the content: posture paragraph, concrete behaviors list, anti-patterns list, followed by `## History` for prior versions.

Invariant: exactly one file per user at `state/show-up.md` with `slug: current`.

**Current version:** 1.

---

## `voice-sample`

A chunk of the user's writing used by comms-generating modules to emulate tone. Owned by `personal-os`.

```yaml
register: string   # required; e.g., casual, formal-internal, board-facing, technical
source: string     # optional; where the sample came from (e.g., "Slack post 2026-03-15")
```

Invariants:
- Files live at `state/voice/{YYYY-MM-DD}.md` (or `{YYYY-MM-DD}-N.md` if multiple in one day).
- `slug` equals the filename stem.
- Body ≥ 100 words (activation gate; runtime skill can relax).

**Current version:** 1.

---

## `retro-personal`

A personal retrospective in 4Ls format (Liked / Learned / Lacked / Longed for). Owned by `personal-os`.

```yaml
period: string     # required; human description of what the retro covers (e.g., "week ending 2026-04-21")
```

Invariants:
- Files live at `state/retros/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.
- Body contains four sections: `## Liked`, `## Learned`, `## Lacked`, `## Longed for`.

Kept module-scoped (vs. a shared `retro` type) until other modules add retros — then consolidate via migration.

**Current version:** 1.

---

## Schema versions

Current canonical version per type.

| Type | Version | Introduced by |
| --- | --- | --- |
| `_module` | 1 | baseline |
| `altitude` | 1 | `personal-os` |
| `goal-horizon` | 1 | `personal-os` |
| `show-up` | 1 | `personal-os` |
| `voice-sample` | 1 | `personal-os` |
| `retro-personal` | 1 | `personal-os` |

Version bumps ship with a migration at `scripts/migrate_{type}_v{N}_to_v{N+1}.py`. The migration runs automatically the next time a surface loads and detects drift; it commits a pre-migration snapshot to git so rollback is `git revert`.
