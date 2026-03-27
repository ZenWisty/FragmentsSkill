---
name: private-DBserver-access
description: Access and manage a private markdown database server via SSH. Use when the user wants to search knowledge bases, review notes, check schedules, retrieve markdown files, or update content on remote servers. Triggers when user mentions 'database server', 'markdown server', SSH file operations, or updating remote notes/knowledge. Also use when user asks to 'tree', 'get', or 'modify' files on a remote server.
---

## Server Registry (Input)

For each server, maintain: **Alias (e.g., db1, mmdb2), User, Host, Port (default 22), ScriptPath**.
- If details are missing, ask the user once and store for the session.
- Run `help` on a new server to discover the latest API.

## First-Time Setup (SSH Key)

Before connecting to a new server for the first time, you MUST add your SSH key:

```bash
ssh-copy-id -p $PORT $USER@$HOST
```

This will prompt for the password once and then install your public key to `~/.ssh/authorized_keys` on the remote server, enabling passwordless SSH access for future connections.

## Core Operations

### Explore (List files)
- **SSH command:** `ssh -p $PORT $USER@$HOST "bash $SCRIPT_PATH tree [subdir]"`
- **Example:** User says "show me what's in the notes folder on db1"
- **Action:** Run tree command for the specified subdirectory

### Retrieve (Read file)
- **SSH command:** `ssh -p $PORT $USER@$HOST "bash $SCRIPT_PATH get <file_path>"`
- **Example:** User says "get the meeting notes from server mmdb2"
- **Action:** Run get command and display the file contents

### Update (Modify file)
- **SSH command:** `cat << 'EOF' | ssh -p $PORT $USER@$HOST "bash $SCRIPT_PATH modify <file_path> <secret> '<msg>'" ... EOF`
- **Example:** User says "add this note to my knowledge base on db1"
- **Action:** Prompt for secret, then execute modify command

## Security Policy

- **Read Operations (`tree`, `get`):** Execute immediately using SSH keys.
- **Write Operations (`modify`):** 
    - MUST prompt the user for the **Modify Secret** every time.
    - NEVER store the secret in memory; it must be provided for each individual write command.
- **Path Protection:** All paths are relative to `~/my_db` on the server.

## Output Format (Tree View)

Display the directory structure using the following visual indentation:
```text
|root_dir
|__file_at_root.md
|__subdirectory
     |__nested_file.md