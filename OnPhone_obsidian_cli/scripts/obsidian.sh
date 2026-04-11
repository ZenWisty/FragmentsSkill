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
        # 列出标签（调用 C++ 索引）
        FILE=$(get_val "path" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total"   && echo "yes")
        SHOW_COUNTS=$(printf '%s\n' "$@" | grep -qx "counts" && echo "yes")
        SORT_COUNT=$(printf '%s\n' "$@" | grep -qx "sort=count" && echo "yes")

        export OBSIDIAN_VAULT_PATH="$VAULT_PATH"
        ARGS="tags"
        [ -n "$FILE" ]     && ARGS="$ARGS --path=$FILE"
        [ "$TOTAL_ONLY" == "yes" ]    && ARGS="$ARGS --total"
        [ "$SHOW_COUNTS" == "yes" ]   && ARGS="$ARGS --counts"
        [ "$SORT_COUNT" == "yes" ]    && ARGS="$ARGS --sort=count"

        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        "$SCRIPT_DIR/obsidian_cli" $ARGS
        ;;

    "tag")
        # 搜索含特定标签的文件（调用 C++ 索引）
        TAG=$(get_val "name" "$@")
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total"   && echo "yes")
        VERBOSE=$(printf '%s\n' "$@" | grep -qx "verbose" && echo "yes")

        export OBSIDIAN_VAULT_PATH="$VAULT_PATH"
        ARGS="tag --name=$TAG"
        [ "$TOTAL_ONLY" == "yes" ] && ARGS="$ARGS --total"
        [ "$VERBOSE" == "yes" ]    && ARGS="$ARGS --verbose"

        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        "$SCRIPT_DIR/obsidian_cli" $ARGS
        ;;

    "links")
        # 提取文件中的 outgoing links（排除嵌入文件 ![[...]]）
        # 直接用 bash 参数展开提取 path= 后所有内容（支持含空格路径）
        TOTAL_ONLY=$(printf '%s\n' "$@" | grep -qx "total" && echo "yes")
        # 提取 path= 后的值（允许引号包围）
        for arg in "$@"; do
            case "$arg" in
                path=*)
                    FILE="${arg#path=}"
                    # 去除首尾引号
                    FILE="${FILE#\"}"
                    FILE="${FILE%\"}"
                    FILE="${FILE#\'}"
                    FILE="${FILE%\'}"
                    ;;
            esac
        done

        if [ -z "$FILE" ]; then
            echo "Error: path is required"
            exit 1
        fi

        if [ ! -f "$VAULT_PATH/$FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi

        # 构建 basename → 相对路径 的查找表（一次 find，全局复用）
        # 格式: "basename|relative/path/file.md"
        MAP_FILE="/tmp/obsidian_links_map_$$"
        find "$VAULT_PATH" -name "*.md" | sed "s|^$VAULT_PATH/||" | \
            while IFS= read -r rel; do
                base=$(basename "$rel" .md)
                echo "$base|$rel"
            done > "$MAP_FILE"

        # 用 rg 提取所有链接内容，跳过 ![[...]]（嵌入）
        # Wiki link: [[...]] → 提取目标名，查表找实际路径
        # Markdown link: [text](path) → 直接提取 () 内的路径
        LINKS=$(rg -o '\[\[[^]]*\]\]' "$VAULT_PATH/$FILE" | \
            grep -v '^{{' | \
            sed -n 's/\[\[\(.*\)\]\]/\1/p' | \
            while IFS= read -r inner; do
                # 去掉 |alias，取 | 前的目标部分
                target="${inner%%|*}"
                # 去掉 #heading 或 #^block，取 # 前的目标部分
                target="${target%%#*}"
                # 查表找实际路径（精确匹配 basename）
                match=$(grep "^$target|" "$MAP_FILE" | head -1 | cut -d'|' -f2)
                [ -n "$match" ] && echo "$match" || echo "$target"
            done)

        # Markdown link: [text](path) — 直接提取 () 内的路径
        MD_LINKS=$(rg -on '\[[^]]*\]\([^)]*\.md\)' "$VAULT_PATH/$FILE" | \
            sed -n 's/.*\](\([^)]*\.md\)).*/\1/p')

        # 合并去重（两种链接合并）
        { echo "$LINKS"; echo "$MD_LINKS"; } | grep -v '^$' | sort -u > /tmp/obsidian_links_result_$$
        ALL_LINKS=$(cat /tmp/obsidian_links_result_$$)

        rm -f "$MAP_FILE" /tmp/obsidian_links_result_$$

        if [ "$TOTAL_ONLY" == "yes" ]; then
            RESULT=$(echo "$ALL_LINKS" | wc -l)
            echo "$RESULT"
        else
            echo "$ALL_LINKS"
        fi

        # 后台静默调用 links_verify_remote_backlinks.py
        # 参数：源文件路径 + 所有出链目标路径（多行直接传，由 Python 解析）
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        #nohup python3 -m debugpy --listen 127.0.0.1:5678 --wait-for-client "$SCRIPT_DIR/links_verify_remote_backlinks.py" \
        #    "$FILE" "$ALL_LINKS" > /dev/null 2>&1 &
        nohup python3 "$SCRIPT_DIR/links_verify_remote_backlinks.py" \
            "$FILE" "$ALL_LINKS" > /dev/null 2>&1 &
        ;;

    "backlinks")
        # 查找反链：哪些文档链接到本文件
        # 支持 wiki link [[basename]] 和 markdown link [text](path/to/basename.md)
        for arg in "$@"; do
            case "$arg" in
                path=*)
                    FILE="${arg#path=}"
                    FILE="${FILE#\"}"; FILE="${FILE%\"}"
                    FILE="${FILE#\'}"; FILE="${FILE%\'}"
                    ;;
            esac
        done

        if [ -z "$FILE" ]; then
            echo "Error: path is required"
            exit 1
        fi

        FULL_FILE="$VAULT_PATH/$FILE"
        if [ ! -f "$FULL_FILE" ]; then
            echo "File not found: $FILE"
            exit 1
        fi

        # 提取 basename（不含 .md 扩展名）
        TARGET_NAME=$(basename "$FILE" .md)
        TARGET_FULL_NO_EXT="${FILE%.md}"
        # 目标文件名（带 .md）
        TARGET_WITH_EXT=$(basename "$FILE")

        # 查找 wiki link: [[basename]] 或 [[dir/basename]]
        WIKI_BACKLINKS=$(rg -l "\[\[$TARGET_NAME\]\]" "$VAULT_PATH" 2>/dev/null | \
            grep -v "$FULL_FILE" | \
            sed "s|$VAULT_PATH/||")

        # 查找 markdown link: [text](dir/basename.md) 或 [text](basename.md)
        MD_BACKLINKS=$(rg -l -g '*.md' "\]\($TARGET_WITH_EXT\)\]" "$VAULT_PATH" 2>/dev/null | \
            grep -v "$FULL_FILE" | \
            sed "s|$VAULT_PATH/||")

        # markdown link 也支持不带扩展名的形式 [text](dir/basename)
        MD_BACKLINKS2=$(rg -l -g '*.md' "\]\($TARGET_FULL_NO_EXT\)\]" "$VAULT_PATH" 2>/dev/null | \
            grep -v "$FULL_FILE" | \
            sed "s|$VAULT_PATH/||")

        # 合并去重（两种格式找到的结果）
        { echo "$WIKI_BACKLINKS"; echo "$MD_BACKLINKS"; echo "$MD_BACKLINKS2"; } | \
            grep -v '^$' | sort -u

        # 写入 frontmatter（如果文件中没有 backlinks 字段的话）
        HAS_BACKLINKS_FIELD=$(rg "^backlinks:" "$FULL_FILE" | head -1)
        if [ -z "$HAS_BACKLINKS_FIELD" ]; then
            # 计算出的结果写入 frontmatter
            COMPUTED=$(rg -l "\[\[$TARGET_NAME\]\]" "$VAULT_PATH" 2>/dev/null | \
                grep -v "$FULL_FILE" | \
                sed "s|$VAULT_PATH/||" | sort -u)
            if [ -n "$COMPUTED" ]; then
                # 追加 backlinks 字段到 frontmatter
                python3 -c "
import sys
path = sys.argv[1]
links = sys.argv[2:]
content = open(path, encoding='utf-8').read()
if links:
    fm_line = 'backlinks:'
    new_entries = '\n'.join(f'  - {l}' for l in links)
    if content.startswith('---'):
        # 插入到 frontmatter 末尾（第一个 --- 之后）
        end = content.find('\n---', 4)
        if end != -1:
            new_content = content[:end] + '\n' + fm_line + '\n' + new_entries + content[end:]
        else:
            new_content = content
    else:
        new_content = '---\n' + fm_line + '\n' + new_entries + '\n---\n' + content
    open(path, 'w', encoding='utf-8').write(new_content)
" "$FULL_FILE" "$COMPUTED"
            fi
        fi
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
