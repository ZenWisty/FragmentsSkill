#!/bin/bash

# ================== 1. 防重复启动锁（PID文件法）============
PID_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/vault_monitor.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️ Vault 监控服务已经在后台运行中了 (PID $OLD_PID)，请勿重复启动！"
        exit 1
    fi
    echo "旧 PID 文件残留，已清理"
fi
echo $$ > "$PID_FILE"
# ==================================================

VAULT="/storage/emulated/0/MyObsidianVaults/md_db"

echo "👀 正在静默监控 .md 文件的改动..."

inotifywait -m -r \
    -e close_write,moved_to \
    --exclude '/\.(obsidian|git)/' \
    --format '%w%f' "$VAULT" |
while read -r FILE; do
    if [[ "$FILE" == *.md ]]; then
        echo "📝 拦截到被修改的笔记: $FILE"
        
        # 【核心操作】调用你写好的外部脚本，并把 $FILE 作为参数传给它
        # 注意："$FILE" 两边必须要加双引号！(见下方防坑技巧1)
        python "$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts/scan_task_in_file.py" "$FILE"

        # (可选) Git 同步，可以放在这里
        # cd "$VAULT" && git add . && git commit -m "Auto process" 
		# git push
        
        # 防抖处理：冷却 2 秒，防止单次保存触发多次脚本
        sleep 2
    fi
done