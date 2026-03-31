#!/bin/bash
# --- 配置区 ---
MD_DB_PATH="$HOME/storage/shared/MyObsidianVaults/md_db"

# --- 参数检查 ---
if [ -z "$1" ]; then
    echo "用法: obsidian_search_file.sh <filename>"
    exit 1
fi

SEARCH_NAME="$1"

# --- 在 md_db 中搜索文件 ---
RESULTS=$(find "$MD_DB_PATH" -type f -iname "*${SEARCH_NAME}*" 2>/dev/null)

# --- 返回结果 ---
if [ -z "$RESULTS" ]; then
    echo "未找到包含 '$SEARCH_NAME' 的文件"
    exit 1
else
    echo "$RESULTS" | while read -r filepath; do
        # 提取相对于 md_db 的路径
        REL_PATH="${filepath#$MD_DB_PATH/}"
        echo "$REL_PATH"
    done
fi
