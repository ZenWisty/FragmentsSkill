# Obsidian Tag Search Reference

This guide explains how to use `rg` (ripgrep) to search for tags in an Obsidian vault.

## Vault Path

Default vault: `$HOME/storage/shared/MyObsidianVaults/md_db`
Reference this path as `$VAULT_PATH` in commands.

## A. Basic Search (filename + line number + matching line)

Search for a tag (e.g., `#todo`) across all files:

```bash
rg -n -i "#todo" "$VAULT_PATH"
```

- `-n`: Show line numbers
- `-i`: Case insensitive
- Output format: `filename:line_number:matching_content`

## B. Get Context (lines before and after the tag)

To see lines surrounding the tag (e.g., 2 lines before, 3 lines after):

```bash
rg -n -i -B 2 -A 3 "#todo" "$VAULT_PATH"
```

- `-B N`: Show N lines Before the match
- `-A N`: Show N lines After the match
- Output includes the context lines with their line numbers

## C. Search Only Markdown Files

Limit search to `.md` files only (excludes images, attachments):

```bash
rg -t md -i "#todo" "$VAULT_PATH"
```

- `-t md`: Search only in Markdown file type

Combine with other options:

```bash
rg -n -t md -i -B 1 -A 1 "#todo" "$VAULT_PATH"
```

## Search Range Limitation

User can specify a subdirectory within the vault. For example, `/tmp` means `$VAULT_PATH/tmp`:

```bash
rg -n -i "#todo" "$VAULT_PATH/tmp"
```

## Output Format Requirements

The search result **MUST** contain:
1. **File relative path** (from vault root)
2. **Line number**
3. **Matching content** (the line itself)

Example output:
```
tmp/notes.md:15:#todo implement feature X
```

## Handling Multiple Results

If search returns multiple matches:

1. **List ALL results** clearly with index numbers
2. **Do NOT auto-select** — ask the user which result they want to use
3. Wait for user confirmation before proceeding with any file

Example prompt to user:
```
Found 3 matches for #todo:
1. tmp/notes.md:15 - #todo implement feature X
2. work/projects.md:42 - #todo review PR
3. daily/2024-01-15.md:8 - #todo call John

Which one would you like to open? (1/2/3)
```
