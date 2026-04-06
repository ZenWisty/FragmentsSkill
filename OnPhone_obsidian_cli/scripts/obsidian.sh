#!/bin/bash

# ==============================
# Obsidian CLI for Android/Termux
# ==============================
# 动作类 → Advanced URI (am start)
# 查询类 → 本地文件操作 (rg/cat/find/git)
#
# 依赖:
#   - ripgrep (rg)
#   - git
#   - coreutils (stat, wc)
#   - Advanced URI 插件 (Obsidian 中安装)
# ==============================

# --- 配置区（必须修改） ---
VAULT="md_db"
VAULT_PATH="$HOME/storage/shared/MyObsidianVaults/md_db"
# -------------------------

cd "$VAULT_PATH" || exit 1

# 参数解析辅助函数
# 从 "name=todo" 或 'name="todo"' 中提取值
# get_val() {
#     echo "$*" | grep -oP "$1=\"?\K[^\" ]+"
# }
get_val() {
    local key=$1
    shift
    local input="$*"
    # 优先匹配引号内的值，其次匹配无引号的值
    echo "$input" | grep -oP "$key=\"\K[^\"]+|(?<=$key=)[^\" ]+"
}

command=$1
shift

case "$command" in
    # ============================================================
    # A. 动作类命令 — 通过 Advanced URI 插件
    # ============================================================

    "open")
        # 在 Obsidian 中打开文件
        FILE=$(get_val "path" "$@")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&filepath=$FILE" \
            > /dev/null 2>&1
        echo "Opened: $FILE"
        ;;

    "append")
        # 向文件追加内容
        FILE=$(get_val "path" "$@")
        DATA=$(get_val "content" "$@")
        # 注意: DATA 中特殊字符需 URL 编码
        # URL 编码
        # FILE_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$FILE'''))")
        # DATA_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$DATA'''))")

        echo "FILE: $FILE"
        echo "CONTENT TO APPEND: $DATA"
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&filepath=$FILE&data=$DATA&mode=append" \
            > /dev/null 2>&1
        echo "Appended to: $FILE"
        ;;

    "prepend")
        # 向文件头部插入内容
        FILE=$(get_val "path" "$@")
        DATA=$(get_val "content" "$@")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&filepath=$FILE&data=$DATA&mode=prepend" \
            > /dev/null 2>&1
        echo "Prepended to: $FILE"
        ;;

    "daily")
        # 打开今日日记
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&daily=true" \
            > /dev/null 2>&1
        echo "Opened: Today's daily note"
        ;;

    "command")
        # 执行 Obsidian 内部命令（需知道 commandid）
        CMD_ID=$(get_val "id" "$@")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&commandid=$CMD_ID" \
            > /dev/null 2>&1
        echo "Executed command: $CMD_ID"
        ;;

    "search")
        # 在库中搜索文件内容，返回匹配文件路径
        QUERY=$(get_val "query" "$@")
        if [ -z "$QUERY" ]; then
            echo "Error: query is required"
            exit 1
        fi
        # 搜索 .md 文件内容，返回文件路径（去重）
        rg -l -g '*.md' "$QUERY" "$VAULT_PATH" | sed "s|$VAULT_PATH/||" | sort -u
        ;;

    # "bookmark")
    #     # 打开书签
    #     NAME=$(get_val "name" "$@")
    #     am start -a android.intent.action.VIEW \
    #         -d "obsidian://advanced-uri?vault=$VAULT&bookmark=$NAME" \
    #         > /dev/null 2>&1
    #     echo "Opened bookmark: $NAME"
    #     ;;

    # ============================================================
    # B. 查询类命令 — 通过本地文件操作
    # ============================================================

    "read")
        # 读取文件内容
        FILE=$(get_val "path" "$@")
        if [ ! -f "$VAULT_PATH/$FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi
        cat "$VAULT_PATH/$FILE"
        ;;

    "tags")
        # 列出标签
        FILE=$(get_val "path" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total"   && echo "yes")
        SHOW_COUNTS=$(printf '%s\n' "$@" | grep -qx "counts" && echo "yes")
        SORT_COUNT=$(printf '%s\n' "$@" | grep -qx "sort=count" && echo "yes")

        TARGET=${FILE:-$VAULT_PATH}
        ALL_TAGS=$(rg -ohP "(?<=^|[[:space:]])#[\w/]+" "$TARGET")

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$ALL_TAGS" | sort -u | wc -l
        elif [ "$SHOW_COUNTS" == "yes" ]; then
            RESULT=$(echo "$ALL_TAGS" | sort | uniq -c)
            [ "$SORT_COUNT" == "yes" ] && RESULT=$(echo "$RESULT" | sort -nr)
            echo "$RESULT"
        else
            echo "$ALL_TAGS" | sort -u
        fi
        ;;

    "tag")
        # 搜索含特定标签的文件
        TAG=$(get_val "name" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total"   && echo "yes")
        VERBOSE=$(printf '%s\n' "$@" | grep -qx "verbose" && echo "yes")

        # 匹配 #tag，确保前后是标签边界
        MATCHES=$(rg -i -l "(^|[[:space:]])#$TAG([[:space:]]|$)" "$VAULT_PATH")
        COUNT=$(echo "$MATCHES" | grep -v '^$' | wc -l)

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$COUNT"
        else
            echo "Tag: #$TAG"
            echo "Total Occurrences: $COUNT"
            [ "$VERBOSE" == "yes" ] && echo -e "\nFiles:\n$MATCHES"
        fi
        ;;

    "links")
        # 提取文件中的 [[link]] 链接
        FILE=$(get_val "path" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total" && echo "yes")

        LINKS=$(rg -ohP "\[\[\K[^\]|#]+" "$VAULT_PATH/$FILE")

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$LINKS" | grep -v '^$' | wc -l
        else
            echo "$LINKS"
        fi
        ;;

    "backlinks")
        # 查找反链：哪些文件链接到目标文件
        FILE=$(get_val "path" "$@")
        TARGET=$(basename "$FILE" .md)
        rg -l "\[\[$TARGET\]\]" "$VAULT_PATH"
        ;;

    "file")
        # 获取文件元信息
        FILE=$(get_val "file" "$@")
        FULL_FILE="$VAULT_PATH/$FILE"
        if [ ! -f "$FULL_FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi

        NAME=$(basename "$FILE" .md)
        EXT=$(basename "$FILE" | grep -oP '\.[^.]+$' || echo "")
        SIZE=$(stat -c %s "$FULL_FILE")
        # %W 创建时间（不可用则显示 -）
        CREATED=$(stat -c %W "$FULL_FILE" 2>/dev/null || echo "-")
        # %Y 修改时间（纳秒级时间戳）
        MODIFIED=$(stat -c %Y "$FULL_FILE")

        # 按指定格式输出，键名宽度 10，值左对齐
        printf "%-10s %s\n" "path" "$FILE"
        printf "%-10s %s\n" "name" "$NAME"
        printf "%-10s %s\n" "extension" "$EXT"
        printf "%-10s %s\n" "size" "$SIZE"
        printf "%-10s %s\n" "created" "$CREATED"
        printf "%-10s %s\n" "modified" "$MODIFIED"
        ;;

    "files")
        # 列出文件
        FOLDER=$(get_val "folder" "$@")
        EXT=$(get_val "ext" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total" && echo "yes")

        TARGET=${FOLDER:-$VAULT_PATH}
        PATTERN="*${EXT:-}"
        FILES=$(find "$TARGET" -type f -name "$PATTERN" | sed 's|^\./||')

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$FILES" | grep -v '^$' | wc -l
        else
            echo "$FILES"
        fi
        ;;

    "folder")
        # 文件夹信息
        DIR=$(get_val "path" "$@")
        FULL_DIR="$VAULT_PATH/$DIR"
        if [ ! -d "$FULL_DIR" ]; then
            echo "Folder not found: $DIR"
            exit 1
        fi

        # 文件夹名称（不带路径）
        DIR_NAME=$(basename "$DIR")
        # 子文件数（不含自身）
        FILE_COUNT=$(find "$FULL_DIR" -type f | wc -l)
        # 子文件夹数（不含自身）
        FOLDER_COUNT=$(find "$FULL_DIR" -type d | wc -l)
        FOLDER_COUNT=$((FOLDER_COUNT - 1))
        # 总大小（KB）
        TOTAL_SIZE=$(du -sk "$FULL_DIR" | cut -f1)

        printf "%-10s %s\n" "path" "$DIR_NAME"
        printf "%-10s %s\n" "files" "$FILE_COUNT"
        printf "%-10s %s\n" "folders" "$FOLDER_COUNT"
        printf "%-10s %s\n" "size" "$TOTAL_SIZE"
        ;;

    "folders")
        # 列出所有子文件夹（递归，含深层文件夹）
        # vault 文件夹本身显示为 /
        PARENT=$(get_val "folder" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total" && echo "yes")

        TARGET=${PARENT:-$VAULT_PATH}

        # 递归查找所有文件夹，-path/-prune 在顶层就排除 .git/.obsidian/.claude/.trash
        # vault 本身显示为 /
        FOLDERS=$(find "$TARGET" -type d \
            \( -path "*/.git" -o -path "*/.obsidian" -o -path "*/.claude" -o -path "*/.trash" \) -prune -o \
            -type d -print | \
            sed "s|^$VAULT_PATH||" | \
            while IFS= read -r relpath; do
                # 跳过隐藏文件夹（以 . 开头）
                dir=$(basename "$relpath")
                case "$dir" in
                    .*) continue ;;
                esac
                # vault 本身显示为 /
                [ -z "$relpath" ] && echo "/" || echo "$relpath"
            done | grep -v '^$')

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$FOLDERS" | wc -l
        else
            echo "$FOLDERS"
        fi
        ;;

    "outline")
        # 提取文件大纲（标题树）
        FILE=$(get_val "path" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total" && echo "yes")

        if [ ! -f "$VAULT_PATH/$FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi

        HEADINGS=$(grep -nP "^#+ " "$VAULT_PATH/$FILE")

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$HEADINGS" | wc -l
        else
            echo "$HEADINGS" | while read -r line; do
                LEVEL=$(echo "$line" | grep -o "#" | wc -l)
                TEXT=$(echo "$line" | sed 's/^.*#\+ //')
                LNUM=$(echo "$line" | cut -d: -f1)
                printf "%$(( (LEVEL-1)*2 ))s- %s (line %s)\n" "" "$TEXT" "$LNUM"
            done
        fi
        ;;

    "move")
        # 移动文件（优先 git mv 保持历史）
        FROM=$(get_val "path" "$@")
        TO=$(get_val "to" "$@")

        if [ -d "$VAULT_PATH/.git" ]; then
            git -C "$VAULT_PATH" mv "$FROM" "$TO" && echo "Git Moved: $FROM -> $TO"
        else
            mv "$VAULT_PATH/$FROM" "$VAULT_PATH/$TO" && echo "Moved: $FROM -> $TO"
        fi
        ;;

    *)
        echo "=== Obsidian CLI (Android/Termux) ==="
        echo ""
        echo "动作类 (Advanced URI):"
        echo "  obsidian open      path=\"Note.md\""
        echo "  obsidian append    path=\"Note.md\" content=\"text\""
        echo "  obsidian prepend   path=\"Note.md\" content=\"text\""
        echo "  obsidian daily"
        echo "  obsidian command   id=\"plugin-command-id\""
        echo "  obsidian search    query=\"keyword\""
        # echo "  obsidian bookmark  name=\"bookmark-name\""
        echo ""
        echo "查询类 (本地文件):"
        echo "  obsidian read      path=\"Note.md\""
        echo "  obsidian tags      [path=\"file.md\"] [total] [counts] [sort=count]"
        echo "  obsidian tag       name=\"todo\" [total] [verbose]"
        echo "  obsidian links     path=\"Note.md\" [total]"
        echo "  obsidian backlinks path=\"Note.md\""
        echo "  obsidian file      path=\"Note.md\""
        echo "  obsidian files     [folder=\"path\"] [ext=\".pdf\"] [total]"
        echo "  obsidian folder    path=\"Dir\" [info=files|folders|size]"
        echo "  obsidian folders   [folder=\"path\"] [total]"
        echo "  obsidian outline   path=\"Note.md\" [total]"
        echo "  obsidian move      path=\"A.md\" to=\"Folder/A.md\""
        ;;
esac
