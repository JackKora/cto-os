---
name: data-backup
description: "Activates for offsite backup of the CTO OS data repo to Google Drive — zipping the entire data repo (including `.git/` history) and uploading to a user-configured Drive folder, with automatic pruning of older backups to a configured retention count. Covers: first-time setup (choosing the Drive folder and retention count), running an on-demand backup, rescheduling or updating the backup configuration, and reviewing the upload history. Also activates on oblique phrasings like 'back up my data,' 'upload a backup to Drive,' 'push the data repo to Drive,' 'snapshot cto-os-data,' 'change how many backups I keep.' Does NOT activate on git-side backup (user-operated `git push`), cloud-drive folder sync (OS-level; the user sets that up outside the skill), or backups of anything other than the cto-os-data repo."
requires: []
optional: []
---

# Data Backup

## Scope

Offsite backup of the CTO OS data repo. The sole verb this module owns: zip the entire data repo (`.git/` included so history survives) and upload the archive to a Google Drive folder the user picked once at activation. Every run appends a log entry and prunes older backups from Drive to the configured retention count. Designed to run unattended from Cowork on a schedule; also invokable on demand from Chat or Code.

## Out of scope

- **Git-side backup** — pushing `cto-os-data` to a private git remote is user-operated outside this module. Run in parallel if you want both.
- **Cloud-drive folder sync** — placing `cto-os-data` inside a synced Google Drive / iCloud / Dropbox folder is an OS-level setup, not something this module manages.
- **Backing up anything other than `cto-os-data`** — if you want to archive the skill repo, use plain `git push`; the skill repo isn't user state.
- **Restore** — out of scope. Restoration from a zip is a manual unzip into a fresh `cto-os-data` location.

## Frameworks

This module has no external framework — it's an infrastructure concern (zip + upload + prune). Design invariants instead:

- **Include history.** The archive contains `.git/` so the backup is self-sufficient — you can clone from it, inspect past state, recover from mis-writes. Excluding `.git/` would be a hidden gotcha.
- **Exclude ephemera.** `logs/`, `integrations-cache/`, `.backups/`, `.DS_Store`, `.env*` — regenerable, cruft, or secrets that must never leave local disk.
- **Delete local after upload.** The local zip is a staging file, not a second backup. Keeping it would waste disk; deleting it keeps the data repo clean for the next run.
- **Prune on success only.** If an upload fails, don't touch the prior Drive state — the user still has their last-known-good set.
- **Operate only on our own files.** Pruning matches Drive file IDs this skill uploaded (recorded in the local log). Never touches anything in the Drive folder we didn't put there.

## Triggers

- "back up my data"
- "run the backup"
- "upload a backup to Drive"
- "push cto-os-data to Drive"
- "take a snapshot"
- "change the backup folder"
- "change how many backups I keep"
- "show my backup history"
- Oblique: "I'm worried about losing this laptop — is everything backed up?"
- Oblique: "what's the latest backup?"

## Activation flow

Running this flow populates baseline configuration. Each step writes one concrete artifact; resumption is implicit (if the target field is populated, the step is done).

### 1. Choose the Drive destination folder

**Ask:** "Where in Google Drive should backups land? Pick an existing folder or name a new one — I'll look it up or create it via the Drive connector. Backups are sensitive, so this should be a private folder only you can access."
**Writes:** `cto-os-data/modules/data-backup/state/config.md` with `type: backup-config`, `slug: current`, `drive_folder_id`, `drive_folder_name`.
**Expects:** frontmatter has both `drive_folder_id` (Drive's opaque ID) and `drive_folder_name` (human label) set.

### 2. Choose retention count

**Ask:** "How many of the most recent backups should I keep in Drive? Older ones get pruned after each new upload — you won't accumulate forever. Typical values: 7 for daily-scheduled, 4–8 for weekly-scheduled. This is a hard count, not a time window."
**Writes:** updates `cto-os-data/modules/data-backup/state/config.md` — adds `retain_count: <int>` to the same frontmatter.
**Expects:** `retain_count` is a positive integer.

### 3. Verify end-to-end (optional)

**Ask:** "Run one backup now to confirm the zip → upload → prune path works? Takes under a minute on a typical-size data repo."
**Writes:** on confirmation, invokes the `backup-to-drive` skill once. Appends the first entry to `state/uploads.md`.
**Expects:** `uploads.md` exists with at least one entry of `status: uploaded`, OR the user explicitly declines (step still marks complete in `_module.md`).

## Skills

### `backup-to-drive`

**Purpose:** Zip the data repo, upload to the configured Drive folder, prune Drive down to `retain_count`, and log the run.

**Triggers:**
- "back up my data" / "run the backup"
- "take a snapshot" / "upload to Drive"
- Scheduled (Cowork) — no trigger phrase; the schedule invokes this directly.

**Reads:**
- `cto-os-data/modules/data-backup/state/config.md` (destination folder, retention count)
- `cto-os-data/modules/data-backup/state/uploads.md` (prior upload entries — used for the prune step)

**Writes:**
- Transient zip at `cto-os-data/.backups/cto-os-data-{timestamp}.zip` via `run_script zip_data`, deleted after successful upload.
- `cto-os-data/modules/data-backup/state/uploads.md` — appends a new entry to the log body and bumps frontmatter counters (`last_upload`, `upload_count`).

**Flow:**
1. Read `config.md`. If `drive_folder_id` or `retain_count` is missing, fall back to the activation flow.
2. Invoke `run_script zip_data --args '{}'`. Capture `zip_path`, `size_bytes`, `file_count`.
3. Upload the file at `zip_path` to the configured Drive folder (via the Drive connector's `create_file` tool — pass filename, parent folder ID, and the local path).
4. On upload success:
   a. Delete the local zip (`zip_path`).
   b. Append a new log entry to `uploads.md` with `status: uploaded`, the timestamp, size, Drive file ID, and Drive URL.
   c. **Retention sweep.** Read existing log entries where `status: uploaded`, sort by `uploaded_at` desc, take the set beyond position `retain_count`. For each, call the Drive connector's delete/trash on its `drive_file_id`, then rewrite that log entry's `status: pruned` and add `pruned_at`. Only ever operates on entries we logged — never touches files in the Drive folder this skill didn't upload.
5. On upload failure:
   a. Keep the local zip for retry/inspection.
   b. Append a log entry with `status: upload_failed` plus the error.
   c. **Do not run the prune step** — preserves the prior Drive state unchanged.

### `update-backup-config`

**Purpose:** Change the Drive destination folder, the retention count, or both.

**Triggers:**
- "change the backup folder"
- "move backups to a different folder"
- "change how many backups I keep"
- "keep 14 backups instead" / "only keep 3 backups"

**Reads:**
- `cto-os-data/modules/data-backup/state/config.md` (current values)

**Writes:** `cto-os-data/modules/data-backup/state/config.md` — overwrite-with-history. Prior values captured in the body's `## History` section with the change date.

### `show-backup-history`

**Purpose:** Summarize recent backup activity — last run, retention state, any failures.

**Triggers:**
- "show my backup history"
- "when was the last backup"
- "any backup failures"
- "what's in the Drive backup folder"

**Reads:**
- `cto-os-data/modules/data-backup/state/uploads.md`
- `cto-os-data/modules/data-backup/state/config.md`

**Writes:** —

## Persistence

- **`cto-os-data/modules/data-backup/state/config.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: backup-config, slug: current, updated: <date>, drive_folder_id: <string>, drive_folder_name: <string>, retain_count: <int>`. Body: rationale for the choices + `## History` with prior versions when config changes.
- **`cto-os-data/modules/data-backup/state/uploads.md`** — singleton (`slug: current`), append-to-body log. Frontmatter: `type: backup-log, slug: current, updated: <date>, last_upload: <datetime, optional>, upload_count: <int>`. Body: reverse-chronological log of upload events, each one an entry with `upload_id`, `uploaded_at`, `size_bytes`, `file_count`, `drive_file_id`, `drive_file_url`, `status` (`uploaded` | `pruned` | `upload_failed`), optional `pruned_at`, optional `error`.
- **`cto-os-data/.backups/cto-os-data-{timestamp}.zip`** — transient staging archive produced by `run_script zip_data`. Not user state, not tracked by git (`.backups/` is gitignored), not writable via MCP's `write_file` / `append_to_file` (forbidden prefix). Deleted after a successful upload; retained on upload failure so the user can retry or inspect. The `backup-to-drive` skill is the only producer; `zip_data` the only writer.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none for `uploads.md` — every run produces a concrete log entry without asking. `config.md` writes prompt for confirmation only when the user is changing the Drive folder (destination changes deserve a deliberate "yes"); retention-count updates save silently.

## State location

`cto-os-data/modules/data-backup/state/`
