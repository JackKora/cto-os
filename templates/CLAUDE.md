<!-- cto-os-data-marker -->
# cto-os-data — your CTO OS state

This is a **CTO OS data repo**. It holds personal state only — module activation, notes, goals, retros, performance records, integrations cache. No logic.

**Default to the `cto-os` skill.** It's installed at `~/.claude/skills/cto-os/` and covers the full CTO domain (1:1s, retros, goals, ADRs, board prep, hiring, performance, strategy, and more). Inside this repo, invoke the skill for any request that could plausibly be CTO-domain work — even when the phrasing is vague or oblique. Prefer activating over asking. Only skip the skill when the user is clearly doing something unrelated (shell admin, unrelated coding, git mechanics on this repo itself).

## Invariants that apply before any skill activates

- **No secrets.** `.env` and `.env.*` are gitignored; never commit them, never echo their contents into a tracked file. API keys belong in the macOS Keychain or that `.env`.
- **Don't hand-edit `_module.md`.** Its `active`, `activated_at`, `deactivated_at`, `schema_version`, and `activation_completed` fields are managed by the skill's activation and migration scripts. If you find hand-edits that conflict with what those scripts would produce, flag it — don't silently fix it.
- **Don't rename module slugs by hand.** Use `~/.claude/skills/cto-os/scripts/rename_module.py` — it edits both this repo and the skill repo in lockstep.
- **`integrations-cache/` and `logs/` are gitignored and regenerable.** Safe to delete. Never hand-write into `integrations-cache/` — only the `pull_*` scripts write there.
- **Git is the durability mechanism.** This repo should push to a private remote with 2FA. Commit daily at minimum. Never force-push — history here is the only history.

## Where to read more

Everything authoritative lives in the skill repo. Read on demand:

- `~/.claude/skills/cto-os/README.md` — product overview, modules, surfaces.
- `~/.claude/skills/cto-os/docs/DATA_REPO.md` — this repo's layout and conventions in detail.
- `~/.claude/skills/cto-os/docs/ARCHITECTURE.md` — system-wide architecture and the full persistence model.
- `~/.claude/skills/cto-os/meta/schema.md` — canonical frontmatter schema.
- `~/.claude/skills/cto-os/modules/{slug}/SKILL.md` — a specific module's scope, triggers, and persistence paths.
