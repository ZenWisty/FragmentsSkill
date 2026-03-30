---
name: on-phone-md-modifier-obsidian
description: Open and edit markdown files in Obsidian vault on Android. Use this skill whenever a user wants to work with markdown files in Obsidian — whether they want to modify an existing note, create new content, or simply view a file. This skill decides which underlying script to invoke based on the user's intent: `obsidian_modifier_nohop.sh` for editing sessions (auto-commits after 20min idle + monitors for changes), `obsidian_viewfile.sh` for pure viewing (quick open, no tracking). Triggers on requests like "open file X in Obsidian", "edit my notes", "view the meeting notes", "modify the daily note", "open in Obsidian", or any mention of opening/viewing/editing .md files in Obsidian vault.
---

# OnPhone Md Modifier - Obsidian Handler

This skill manages opening markdown files in Obsidian on Android with two modes based on user intent.

## Scripts Location

- **Modifier script**: `scripts/obsidian_modifier_nohop.sh` — for editing sessions
- **Viewer script**: `scripts/obsidian_viewfile.sh` — for read-only viewing

## Decision Logic

### Use `obsidian_modifier_nohop.sh` when the user wants to:
- **Modify** or **edit** a file
- Make changes to notes
- Create new content
- Any workflow where saving and syncing matters

**Behavior**: Launches Obsidian, daemonizes, waits 20 minutes, then monitors for file changes every 10 minutes. Auto-commits and pushes via git when idle.

### Use `obsidian_viewfile.sh` when the user wants to:
- **View** or **look at** a file
- Quickly check content
- Read without editing intent
- Jump to a specific line number

**Behavior**: Opens file directly in Obsidian via URI scheme. No background monitoring, no auto-commit.

## Usage

### Opening a file for editing
```bash
scripts/obsidian_modifier_nohop.sh "path/to/file.md"
```

### Opening a file for viewing
```bash
scripts/obsidian_viewfile.sh "path/to/file.md"
```

### Opening at specific line (view only)
```bash
scripts/obsidian_viewfile.sh "path/to/file.md" 42
```

## Implementation Notes

- Both scripts use `am start` to launch Obsidian via Android Intent
- `obsidian_modifier_nohop.sh` uses `nohup` to detach and runs `git pull` before opening
- `obsidian_viewfile.sh` supports the Advanced URI plugin for line jumping
- Vault configuration is hardcoded in scripts: vault name `md_db`, path `$HOME/storage/shared/MyObsidianVaults/md_db`
