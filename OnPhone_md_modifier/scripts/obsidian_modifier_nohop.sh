#!/bin/bash

# --- 配置区 ---
VAULT_NAME="md_db"
DEFAULT_FILE="base.md"

TARGET_FILE="${1:-$DEFAULT_FILE}"
ENCODED_FILE=$(echo "$TARGET_FILE" | sed 's/ /%20/g')
URI="obsidian://open?vault=${VAULT_NAME}&file=${ENCODED_FILE}"

echo "[*] 正在唤起 Obsidian..."
am start -a android.intent.action.VIEW -d "$URI" --user 0 > /dev/null 2>&1

echo "[+] 已打开: $TARGET_FILE"
