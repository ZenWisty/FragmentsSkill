#!/usr/bin/env bash
#
# review_notification_daemon.sh
# 后台运行：读取 review_pending.json，为每个任务显示通知
# 使用 termux-notification 的按钮触发 complete/skip 回调
#
PID_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/notification_daemon.pid"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/data/data/com.termux/files/usr/bin:$HOME/bin:$PATH"
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# 单例检查
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "通知服务已在运行 (PID $OLD_PID)"
        exit 1
    fi
fi
echo $$ > "$PID_FILE"

PENDING_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/review_pending.json"
NOTIF_DIR="/data/data/com.termux/files/usr/bin"
TERMUX_NOTIF="$NOTIF_DIR/termux-notification"
NOTIF_REMOVE="$NOTIF_DIR/termux-notification-remove"
PYTHON_BIN="/data/data/com.termux/files/usr/bin/python3"
ACTION_HANDLER="/data/data/com.termux/files/home/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts/action_handler.py"

echo "通知服务已启动，监听 $PENDING_FILE"

while true; do
    # 读取所有 pending 任务
    if [ ! -f "$PENDING_FILE" ] || [ "$(cat "$PENDING_FILE")" = "[]" ] || [ "$(cat "$PENDING_FILE")" = "" ]; then
        "$NOTIF_REMOVE" all 2>/dev/null
        # 等待文件变化（最多等待5分钟）
        if [ -f "$PENDING_FILE" ]; then
            inotifywait -q -t 300 -e close_write "$PENDING_FILE" 2>/dev/null || true
        else
            inotifywait -q -e create "$(dirname "$PENDING_FILE")"
        fi
        continue
    fi

    TASK_COUNT=$(jq '. | length' "$PENDING_FILE" 2>/dev/null || echo 0)

    for (( i=0; i<TASK_COUNT; i++ )); do
        TASK=$(jq ".[$i]" "$PENDING_FILE" 2>/dev/null)
        if [ -z "$TASK" ] || [ "$TASK" = "null" ]; then continue; fi

        TASK_ID=$(echo "$TASK" | jq -r '.task_id // empty')
        TASK_PATH=$(echo "$TASK" | jq -r '.path // empty' | xargs basename)
        TASK_TIME=$(echo "$TASK" | jq -r '.task_time // empty')

        if [ -z "$TASK_ID" ]; then continue; fi

        # NONCE 同时作为通知 ID 和移除参数（保持一致）
        NONCE=$(date +%s%N)

        # 按钮 action：先移除通知，再调用 python 脚本
        "$TERMUX_NOTIF" \
            --id "$NONCE" \
            --title "[复习] $TASK_PATH" \
            --content "计划时间: $TASK_TIME" \
            --button1 "完成" \
            --button1-action "$NOTIF_REMOVE $NONCE; $PYTHON_BIN $ACTION_HANDLER complete $NONCE $TASK_ID" \
            --button2 "跳过" \
            --button2-action "$PYTHON_BIN $ACTION_HANDLER skip $NONCE $TASK_ID; $NOTIF_REMOVE $NONCE " \
            --priority high \
            >/dev/null 2>&1 &

        echo "已显示通知: $TASK_PATH (id=$NONCE)"
    done

    sleep 30
done
