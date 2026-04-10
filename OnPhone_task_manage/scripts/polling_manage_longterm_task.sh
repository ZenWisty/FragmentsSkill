#!/usr/bin/env bash

# ================== 1. 防重复启动锁 ==================
PID_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/longterm_poll.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️ 长期任务轮询服务已经在后台运行中了 (PID $OLD_PID)，请勿重复启动！"
        exit 1
    fi
fi
echo $$ > "$PID_FILE"

LONGTERM_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_longterm.json"
TASK_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task.json"

echo "🚀 长期任务轮询服务已启动，开始检查 task_longterm.json ..."

# 如果 longterm 文件不存在，初始化空数组
if [ ! -f "$LONGTERM_FILE" ]; then
    echo "[]" > "$LONGTERM_FILE"
fi

# 主循环：每天 23:40 触发一次，然后 sleep 到次日 23:40
while true; do
    NOW_SEC=$(date +%s)
    NOW_PLUS7_SEC=$((NOW_SEC + 7 * 24 * 3600))

    # ── 读取 longterm 任务数 ─────────────────────────────────────
    TASK_COUNT=$(jq '. | length' "$LONGTERM_FILE" 2>/dev/null || echo 0)

    if [ "$TASK_COUNT" -eq 0 ]; then
        echo "💤 task_longterm.json 为空，等待一天后再次检查..."
    else
        echo "📋 共 $TASK_COUNT 个长期任务，开始检查..."

        MOVED_COUNT=0
        REMAINING="[]"
        TMP_MOVED=$(mktemp)
        echo "[]" > "$TMP_MOVED"  # 初始化为合法 JSON 数组

        # longterm 已按时间排序，只需从前往后找到第一个不在 7 天内的任务就停止
        for (( i=0; i<$TASK_COUNT; i++ )); do
            T_TIME=$(jq -r ".[$i].task_time // empty" "$LONGTERM_FILE")
            if [ -z "$T_TIME" ]; then break; fi

            T_SEC=$(date -d "$T_TIME" +%s 2>/dev/null)

            # 解析失败 → 保留（不break，继续检查后续）
            if [ -z "$T_SEC" ]; then
                ITEM=$(jq ".[$i]" "$LONGTERM_FILE")
                REMAINING=$(echo "$REMAINING" | jq ". + [$ITEM]")
                continue
            fi

            # 任务时间在 7 天窗口内 → 迁移到 task.json
            if [ "$T_SEC" -le "$NOW_PLUS7_SEC" ]; then
                # 用 jq 安全地将元素追加到 TMP_MOVED 数组
                TMP_ITEM=$(mktemp)
                jq ".[$i]" "$LONGTERM_FILE" > "$TMP_ITEM"
                RESULT=$(mktemp)
                jq -n --slurpfile item "$TMP_ITEM" --slurpfile base "$TMP_MOVED" '$base[0] + $item' > "$RESULT"
                mv "$RESULT" "$TMP_MOVED"
                rm -f "$TMP_ITEM"
                MOVED_COUNT=$((MOVED_COUNT + 1))
                echo "  ✅ 迁转任务: $T_TIME"
            else
                # 第一个超过 7 天的任务出现，由于已排序，后面的不必再检查
                echo "  ⏭️ 第 $i 个任务 $T_TIME 尚未到 7 天窗口，后面的跳过"
                break
            fi
        done

        # ── 剩余任务收集（跳过已迁转的，从断点 i 开始全部保留）────
        if [ $i -lt $TASK_COUNT ]; then
            REMAINING=$(jq ".[$i:]" "$LONGTERM_FILE")
        fi

        # ── 写回 longterm ───────────────────────────────────────
        echo "$REMAINING" > "$LONGTERM_FILE"

        # ── 追加到 task.json 末尾 ───────────────────────────────
        if [ "$MOVED_COUNT" -gt 0 ]; then
            if [ ! -f "$TASK_FILE" ]; then
                echo "[]" > "$TASK_FILE"
            fi

            TMP_TASK=$(mktemp)
            jq -n --slurpfile moved "$TMP_MOVED" --slurpfile task "$TASK_FILE" '$task[0] + $moved[0]' > "$TMP_TASK"
            mv "$TMP_TASK" "$TASK_FILE"

            # 迁转后重新按时间排序
            TMP_SORTED=$(mktemp)
            jq 'sort_by(.task_time)' "$TASK_FILE" > "$TMP_SORTED"
            mv "$TMP_SORTED" "$TASK_FILE"

            echo "✅ 已将 $MOVED_COUNT 个长期任务迁转到 task.json"
        else
            echo "💤 没有需要迁转的任务"
        fi

        rm -f "$TMP_MOVED"
    fi

    # ── 计算到次日 23:40 的秒数 ────────────────────────────────
    NEXT_SEC=$(date -d "$(date +%Y-%m-%d) 23:40:00" +%s)
    NEXT_SEC=$((NEXT_SEC + 86400))
    SLEEP_SEC=$((NEXT_SEC - NOW_SEC))

    if [ "$SLEEP_SEC" -gt 0 ]; then
        echo "⏳ 下次检查: $(date -d "@$NEXT_SEC" '+%Y-%m-%d %H:%M:%S') (约 $((SLEEP_SEC / 3600)) 小时后)"
        sleep "$SLEEP_SEC"
    else
        echo "⚠️ 下次时间计算异常，1 小时后重试..."
        sleep 3600
    fi
done
