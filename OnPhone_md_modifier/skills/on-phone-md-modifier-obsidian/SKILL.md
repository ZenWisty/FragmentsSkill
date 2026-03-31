---
name: on-phone-md-modifier-obsidian
description: Open, view, edit, and search markdown files in Obsidian vault on Android. Use this skill whenever a user wants to work with markdown files in Obsidian — whether they want to search for a file by name, search for tags within files, modify an existing note, or simply view a file. This skill decides which underlying script or command to invoke based on the user's intent. Triggers on requests like "search tags in obsidian", "search for X in Obsidian", "view file X in obsidian", "open file X in Obsidian", "edit my notes", "modify the daily note", or any mention of opening/viewing/editing/searching .md files in Obsidian vault.
---

# OnPhone Md Modifier - Obsidian Handler

This skill manages opening and searching markdown files in Obsidian on Android with multiple modes based on user intent.

## Setup: Create the `obsview` Symlink

Before using, create a symlink in Termux:

```bash
ln -s /data/data/com.termux/files/home/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_md_modifier/scripts/obsidian_viewfile.sh $PREFIX/bin/obsview
chmod +x $PREFIX/bin/obsview
```

## Decision Logic

### Tag Search: "search tags in obsidian" (STRICT TRIGGER)

**Trigger**: ONLY when user explicitly says "search tags in obsidian" or "search for tags in obsidian".

**Reference**: Read `scripts/obsidian_search_tag.md` for rg command usage.

**Vault path**: `$HOME/storage/shared/MyObsidianVaults/md_db`

**Commands**:
```bash
# Basic search (file:line:content)
rg -n -i "TAG_NAME" "$VAULT_PATH"

# With context (-B before, -A after)
rg -n -i -B 2 -A 3 "TAG_NAME" "$VAULT_PATH"

# Only markdown files
rg -n -t md -i "TAG_NAME" "$VAULT_PATH"

# Limit to subdirectory (e.g., /tmp means $VAULT_PATH/tmp)
rg -n -i "TAG_NAME" "$VAULT_PATH/tmp"
```

**Output requirements**:
- Must contain: file relative path, line number, matching content
- Format: `filename:line_number:matching_content`

**Multiple results handling**:
1. List ALL results with index numbers
2. Ask user which result to use
3. Do NOT auto-select — wait for user confirmation

### File Name Search: `obsidian_search_file.sh`

- **Search** for a file by name
- Find where a file is located

```bash
scripts/obsidian_search_file.sh "keyword"
# Returns relative paths from md_db root
```

### View: `obsview`

- **View** or **look at** a file
- Quickly check content
- Read without editing intent

### Edit: `obsidian_modifier_nohop.sh`

- **Modify** or **edit** a file
- Make changes to notes
- Auto-commits after 20min idle + monitors changes

## Command Reference

| User says | Command to execute |
|-----------|-------------------|
| "search tags in obsidian" | `rg -n -i "TAG" "$VAULT_PATH"` (read obsidian_search_tag.md) |
| "search for X" / "find X" | `scripts/obsidian_search_file.sh "X"` |
| "view X in Obsidian" | `obsview "X"` |
| "look at X" | `obsview "X"` |
| "open X in Obsidian" (view only) | `obsview "X"` |
| "modify X in Obsidian" | `scripts/obsidian_modifier_nohop.sh "X"` |
| "edit X in Obsidian" | `scripts/obsidian_modifier_nohop.sh "X"` |

## RULES FOR CLAUDE (MANDATORY)

1. **FORBIDDEN**: Do NOT create any temporary `.sh` files or wrapper scripts
2. **FORBIDDEN**: Do NOT use `/tmp` or any temporary directory
3. **FORBIDDEN**: Do NOT write scripts inline — call commands directly
4. **STRICT**: Execute `obsview` or scripts directly in a single terminal command
5. For tag search, read `scripts/obsidian_search_tag.md` first before running rg commands
6. Tag search results must list ALL matches and ask user which to proceed with

## Implementation Notes

- All scripts use `am start` to launch Obsidian via Android Intent
- `obsidian_modifier_nohop.sh` uses `nohup` to detach and runs `git pull` before opening
- Vault configuration: vault name `md_db`, path `$HOME/storage/shared/MyObsidianVaults/md_db`
