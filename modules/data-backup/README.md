# Data Backup

**Scope:** Offsite backup of the CTO OS data repo via zip-and-upload to Google Drive. Zips the entire data repo (including `.git/` so history survives), uploads to a configured Drive folder, logs the run, and prunes older backups to a user-chosen retention count. Designed to run unattended from Cowork on a schedule; also invokable on demand from Chat or Code.

**Out of scope:** Git-side backup (`git push` to a private remote — run in parallel if you want both); cloud-drive folder sync (OS-level sync of `cto-os-data` into a Drive / iCloud / Dropbox folder is a setup the user configures outside the skill); backup of anything other than `cto-os-data`; restore (restoration is a manual unzip into a fresh data-repo location).

**Frameworks:** None. This is an infrastructure module — design invariants instead: `.git/` is included (otherwise the backup isn't self-sufficient); ephemera (`logs/`, `integrations-cache/`, `.backups/`, `.DS_Store`, `.env*`) are always excluded; the local zip is deleted after successful upload; pruning runs only after upload success and only on files this skill itself uploaded.

**Depends on:**
- Required: none
- Optional: none

**Requires:** The Google Drive MCP connector must be hooked up (so Claude can call `create_file` / delete via `file_id`). If the connector is missing at runtime, the skill surfaces a clear error rather than failing silently.

**Example tasks:**
- "Back up my data."
- "Run the backup." *(also scheduled via Cowork — no phrasing needed)*
- "Change the backup folder to 'CTO OS Archive'."
- "Keep 14 backups instead of 7."
- "When was the last backup? Any failures?"

**State location:** `cto-os-data/modules/data-backup/state/`

**Produces two state files:**
- `config.md` — singleton holding the Drive folder and retention count.
- `uploads.md` — singleton holding the append-only log of upload events (each with `status: uploaded` | `pruned` | `upload_failed`).
