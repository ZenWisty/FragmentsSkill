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
VAULT="YourVaultName"
VAULT_PATH="$HOME/storage/shared/Documents/Obsidian"
# -------------------------

cd "$VAULT_PATH" || exit 1

# 参数解析辅助函数
# 从 "name=todo" 或 'name="todo"' 中提取值
get_val() {
    echo "$*" | grep -oP "$1=\"?\K[^\" ]+"
}

command=$1
shift
args="$*"

case "$command" in
    # ============================================================
    # A. 动作类命令 — 通过 Advanced URI 插件
    # ============================================================

    "open")
        # 在 Obsidian 中打开文件
        FILE=$(get_val "path" <<< "$args")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&filepath=$FILE" \
            > /dev/null 2>&1
        echo "Opened: $FILE"
        ;;

    "append")
        # 向文件追加内容
        FILE=$(get_val "path" <<< "$args")
        DATA=$(get_val "content" <<< "$args")
        # 注意: DATA 中特殊字符需 URL 编码
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&filepath=$FILE&data=$DATA&mode=append" \
            > /dev/null 2>&1
        echo "Appended to: $FILE"
        ;;

    "prepend")
        # 向文件头部插入内容
        FILE=$(get_val "path" <<< "$args")
        DATA=$(get_val "content" <<< "$args")
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
        CMD_ID=$(get_val "id" <<< "$args")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&commandid=$CMD_ID" \
            > /dev/null 2>&1
        echo "Executed command: $CMD_ID"
        ;;

    "search")
        # 在 Obsidian 中执行搜索
        QUERY=$(get_val "query" <<< "$args")
        # 空格需替换为 %20
        ENCODED_QUERY=$(echo "$QUERY" | sed 's/ /%20/g')
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&search=$ENCODED_QUERY" \
            > /dev/null 2>&1
        echo "Searched: $QUERY"
        ;;

    "bookmark")
        # 打开书签
        NAME=$(get_val "name" <<< "$args")
        am start -a android.intent.action.VIEW \
            -d "obsidian://advanced-uri?vault=$VAULT&bookmark=$NAME" \
            > /dev/null 2>&1
        echo "Opened bookmark: $NAME"
        ;;

    # ============================================================
    # B. 查询类命令 — 通过本地文件操作
    # ============================================================

    "read")
        # 读取文件内容
        FILE=$(get_val "path" <<< "$args")
        if [ ! -f "$VAULT_PATH/$FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi
        cat "$VAULT_PATH/$FILE"
        ;;

    "tags")
        # 列出标签
        FILE=$(get_val "path" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total"   && echo "yes")
        SHOW_COUNTS=$(echo "$args" | grep -q "counts" && echo "yes")
        SORT_COUNT=$(echo "$args" | grep -q "sort=count" && echo "yes")

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
        TAG=$(get_val "name" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total"   && echo "yes")
        VERBOSE=$(echo "$args" | grep -q "verbose" && echo "yes")

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
        FILE=$(get_val "path" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total" && echo "yes")

        LINKS=$(rg -ohP "\[\[\K[^\]|#]+" "$VAULT_PATH/$FILE")

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$LINKS" | grep -v '^$' | wc -l
        else
            echo "$LINKS"
        fi
        ;;

    "backlinks")
        # 查找反链：哪些文件链接到目标文件
        FILE=$(get_val "path" <<< "$args")
        TARGET=$(basename "$FILE" .md)
        rg -l "\[\[$TARGET\]\]" "$VAULT_PATH"
        ;;

    "file")
        # 获取文件元信息
        FILE=$(get_val "path" <<< "$args")
        if [ ! -f "$VAULT_PATH/$FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi
        SIZE=$(stat -c %s "$VAULT_PATH/$FILE")
        MOD=$(stat -c %y "$VAULT_PATH/$FILE")
        WORDS=$(wc -w < "$VAULT_PATH/$FILE")
        echo "Path: $FILE"
        echo "Size: ${SIZE} bytes"
        echo "Words: $WORDS"
        echo "Modified: $MOD"
        ;;

    "files")
        # 列出文件
        FOLDER=$(get_val "folder" <<< "$args")
        EXT=$(get_val "ext" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total" && echo "yes")

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
        DIR=$(get_val "path" <<< "$args")
        INFO=$(get_val "info" <<< "$args")
        if [ ! -d "$VAULT_PATH/$DIR" ]; then
            echo "Folder not found: $DIR"
            exit 1
        fi

        FULL_DIR="$VAULT_PATH/$DIR"
        case "$INFO" in
            "files")   find "$FULL_DIR" -type f | wc -l ;;
            "folders") find "$FULL_DIR" -type d | wc -l ;;
            "size")    du -sh "$FULL_DIR" | cut -f1 ;;
            *)
                du -sh "$FULL_DIR"
                echo "$(find "$FULL_DIR" -maxdepth 1 | wc -l) items"
                ;;
        esac
        ;;

    "folders")
        # 列出子文件夹
        PARENT=$(get_val "folder" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total" && echo "yes")

        TARGET=${PARENT:-$VAULT_PATH}
        FOLDERS=$(find "$TARGET" -maxdepth 1 -type d | sed 's|^\./||' | grep -v '^\.$')

        if [ "$TOTAL_ONLY" == "yes" ]; then
            echo "$FOLDERS" | grep -v '^$' | wc -l
        else
            echo "$FOLDERS"
        fi
        ;;

    "outline")
        # 提取文件大纲（标题树）
        FILE=$(get_val "path" <<< "$args")
        TOTAL_ONLY=$(echo "$args" | grep -q "total" && echo "yes")

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
        FROM=$(get_val "path" <<< "$args")
        TO=$(get_val "to" <<< "$args")

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
        echo "  obsidian bookmark  name=\"bookmark-name\""
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
