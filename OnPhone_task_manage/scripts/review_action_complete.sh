#!/usr/bin/env bash
#
# review_action_complete.sh
# 用户点击通知"完成"按钮时调用
# 写入 response.json，然后关闭通知
#
set -e

# 确保 Termux 命令在 PATH 中（通知 action 通过 dash -c 调用，PATH 受限）
export PATH="/data/data/com.termux/files/usr/bin:$HOME/bin:$PATH"

RESPONSE_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/review_response.json"
NONCE="$1"      # 通知 NONCE（唯一标识，用于关闭通知）
TASK_ID="$2"    # 任务ID（用于定位 pending 中对应任务）

# 立即打印调试日志（不管后面是否出错）
echo "$(date): complete script started NONCE=$NONCE TASK_ID=$TASK_ID PATH=$PATH" >> /tmp/action_debug.log
PENDING_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/review_pending.json"
NOTIF_DIR="/data/data/com.termux/files/usr/bin"

if [ -f "$PENDING_FILE" ] && [ "$(cat "$PENDING_FILE")" != "[]" ]; then
    # 用 task_id 找到对应的任务（避免通知点击错位问题）
    TASK=$(jq --arg tid "$TASK_ID" '.[] | select(.task_id == $tid) | .' "$PENDING_FILE" 2>/dev/null)

    if [ -n "$TASK" ] && [ "$TASK" != "null" ]; then
        TASK_ID_PENDING=$(echo "$TASK" | jq -r '.task_id // empty')
        TASK_PATH=$(echo "$TASK" | jq -r '.path // empty')
        TASK_TAG=$(echo "$TASK" | jq -r '.tag_content // empty')
        TASK_ACTION=$(echo "$TASK" | jq -r '.action // empty')
        REVIEW_TYPE=$(echo "$TASK" | jq -r '.review_type // empty')

        # 写入 complete 响应
        TMP=$(mktemp)
        jq --arg tid "$TASK_ID_PENDING" \
           --arg path "$TASK_PATH" \
           --arg tag "$TASK_TAG" \
           --arg act "$TASK_ACTION" \
           --arg rtype "$REVIEW_TYPE" \
           '. + [{
               "task_id": $tid,
               "action": "complete",
               "timestamp": now | strftime("%Y-%m-%d %H:%M:%S"),
               "review_type": $rtype,
               "path": $path,
               "tag_content": $tag,
               "action_script": $act
           }]' "$RESPONSE_FILE" 2>/dev/null > "$TMP" || echo "[]" > "$TMP"
        mv "$TMP" "$RESPONSE_FILE"

        # 从 pending 中移除该任务（按 task_id 精确匹配）
        TMP2=$(mktemp)
        jq --arg tid "$TASK_ID_PENDING" 'map(select(.task_id != $tid))' "$PENDING_FILE" > "$TMP2" || echo "[]" > "$TMP2"
        mv "$TMP2" "$PENDING_FILE"

        # 关闭通知
        if [ -n "$NONCE" ]; then
            "$NOTIF_DIR/termux-notification-remove" "$NONCE" 2>/dev/null
        fi
    else
        echo "$(date): complete script called but task_id=$TASK_ID not found in pending" >> /tmp/action_debug.log
    fi
else
    echo "$(date): complete script called but pending empty or missing" >> /tmp/action_debug.log
fi
