#!/usr/bin/env bash

# ================== 1. 防重复启动锁 ==================
PID_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_runner.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️ 调度服务已经在后台运行中了 (PID $OLD_PID)，请勿重复启动！"
        exit 1
    fi
fi
echo $$ > "$PID_FILE"

TASK_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task.json"
ABORT_FILE="$(dirname "$TASK_FILE")/task_abort.json"
REVIEW_PENDING_FILE="$(dirname "$TASK_FILE")/review_pending.json"
REVIEW_RESPONSE_FILE="$(dirname "$TASK_FILE")/review_response.json"
REVIEW_HELPER_SCRIPT="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/ReviewHelperApp/src/reviewhelperapp/app.py"

echo "🚀 动态任务调度服务已启动，正在监听: $TASK_FILE"

# 开启主循环
while true; do
    if [ ! -f "$TASK_FILE" ]; then
        echo "等待 task.json 文件被创建..."
        inotifywait -q -e create "$(dirname "$TASK_FILE")"
        continue
    fi

    # 1. 拿到文件的第一条信息，提取 task_time
    TASK_TIME=$(jq -r '.[0].task_time // empty' "$TASK_FILE" 2>/dev/null)

    if [ -z "$TASK_TIME" ]; then
        echo "💤 任务列表为空，挂起休眠，等待 task.json 更新..."
        inotifywait -q -e close_write "$TASK_FILE"
        continue
    fi

    # 2. 将字符串时间转为 Unix 秒数
    TARGET_SEC=$(date -d "$TASK_TIME" +%s 2>/dev/null)
    
    if [ -z "$TARGET_SEC" ]; then
        echo "⚠️ 时间格式无法识别: $TASK_TIME，等待修正..."
        inotifywait -q -e close_write "$TASK_FILE"
        continue
    fi

    # 3. 计算还差多少秒执行
    CURRENT_SEC=$(date +%s)
    WAIT_SEC=$((TARGET_SEC - CURRENT_SEC))

    # ==================================================
    # 核心逻辑分支：与现在时间只差十分钟以内 (<= 600秒)
    # ==================================================
    if [ "$WAIT_SEC" -le 600 ]; then
        echo "⏰ 距目标时间已不足 10 分钟！将所有到期任务转入 ReviewHelper App..."

        # ==================================================
        # 步骤1：收集所有到期任务（当前时间 <= 任务时间 + 10分钟）
        # ==================================================
        NOW_SEC=$(date +%s)
        TASK_COUNT=$(jq '. | length' "$TASK_FILE")
        DUE_COUNT=0

        for (( i=0; i<$TASK_COUNT; i++ )); do
            T_TIME=$(jq -r ".[$i].task_time // empty" "$TASK_FILE")
            [ -z "$T_TIME" ] && break

            T_SEC=$(date -d "$T_TIME" +%s 2>/dev/null)
            [ -z "$T_SEC" ] && break

            # 任务时间 <= 当前时间 + 600秒 视为到期
            if [ "$T_SEC" -le $((NOW_SEC + 600)) ]; then
                DUE_COUNT=$((i+1))
            else
                break
            fi
        done

        if [ "$DUE_COUNT" -eq 0 ]; then
            echo "没有找到到期任务，跳过..."
            sleep 1
            continue
        fi

        echo "📋 发现 $DUE_COUNT 个到期任务，正在写入待确认队列..."

        # ==================================================
        # 步骤2：提取到期任务，写入 review_pending.json
        # ==================================================
        TMP_DUE=$(mktemp)
        jq --argjson idx "$DUE_COUNT" '.[0:$idx]' "$TASK_FILE" > "$TMP_DUE"

        # 为每个任务生成 UUID 并写入 pending
        python3 - << 'PYEOF'
import json
import sys
import uuid

due_tasks = json.load(open("%s" % "$TMP_DUE"))
pending = []

for task in due_tasks:
    task["task_id"] = str(uuid.uuid4())
    task["added_at"] = "%s" % "$(date +%%Y-%%m-%%d %%H:%%M:%%S)"
    pending.append(task)

with open("%s" % "$REVIEW_PENDING_FILE", "w") as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)

print(f"已写入 {len(pending)} 个任务到 review_pending.json")
PYEOF

        rm -f "$TMP_DUE"

        # ==================================================
        # 步骤3：唤起 ReviewHelper App
        # ==================================================
        echo "🚀 唤起 ReviewHelper App，等待用户交互..."
        am start -n com.obsidian.task/.MainActivity > /dev/null 2>&1 || \
        am start -a android.intent.action.MAIN -n com.obsidian.task > /dev/null 2>&1 || \
        echo "⚠️ 无法唤起 App，请确保 ReviewHelperApp 已安装"

        # ==================================================
        # 步骤4：等待用户操作（最多等10分钟）
        # ==================================================
        echo "⏳ 等待用户完成操作（超时10分钟）..."

        # 用 inotifywait 等待 response 文件变化
        if inotifywait -q -t 600 -e close_write "$REVIEW_RESPONSE_FILE" 2>/dev/null; then
            echo "📥 检测到用户操作响应，开始处理..."
        else
            echo "⏰ 等待超时，视为用户跳过所有任务"
        fi

        # ==================================================
        # 步骤5：读取所有响应，逐个处理
        # ==================================================
        if [ -f "$REVIEW_RESPONSE_FILE" ]; then
            RESPONSE_COUNT=$(jq '. | length' "$REVIEW_RESPONSE_FILE" 2>/dev/null || echo 0)

            for (( r=0; r<$RESPONSE_COUNT; r++ )); do
                RESP_TASK_ID=$(jq -r ".[$r].task_id // empty" "$REVIEW_RESPONSE_FILE")
                RESP_ACTION=$(jq -r ".[$r].action // empty" "$REVIEW_RESPONSE_FILE")
                RESP_REVIEW_TYPE=$(jq -r ".[$r].review_type // empty" "$REVIEW_RESPONSE_FILE")
                RESP_PATH=$(jq -r ".[$r].path // empty" "$REVIEW_RESPONSE_FILE")
                RESP_TAG=$(jq -r ".[$r].tag_content // empty" "$REVIEW_RESPONSE_FILE")
                RESP_ORIG_ACTION=$(jq -r ".[$r].action_script // empty" "$REVIEW_RESPONSE_FILE")

                if [ -z "$RESP_TASK_ID" ] || [ -z "$RESP_ACTION" ] || [ -z "$RESP_PATH" ]; then
                    continue
                fi

                echo "  处理响应: path=$RESP_PATH, action=$RESP_ACTION"

                if [ "$RESP_ACTION" = "complete" ]; then
                    echo "  ✅ 执行完成：$RESP_PATH"
                    # 调用 review_job_launch.py 追加时间戳
                    if [ -n "$RESP_PATH" ] && [ -n "$RESP_TAG" ]; then
                        python3 "$RESP_ORIG_ACTION" "$RESP_PATH" "$RESP_TAG" > /dev/null 2>&1
                    fi
                    # 从 task.json 移除该任务（按 path + tag_content 匹配）
                    TMP_REMOVE=$(mktemp)
                    jq ".[] | select(.path != \"$RESP_PATH\" or .tag_content != \"$RESP_TAG\")" "$TASK_FILE" > "$TMP_REMOVE" || echo "[]" > "$TMP_REMOVE"
                    mv "$TMP_REMOVE" "$TASK_FILE"
                else
                    echo "  ⏭️ 用户跳过：$RESP_PATH"
                    # 从 task.json 移除该任务
                    TMP_REMOVE=$(mktemp)
                    jq ".[] | select(.path != \"$RESP_PATH\" or .tag_content != \"$RESP_TAG\")" "$TASK_FILE" > "$TMP_REMOVE" || echo "[]" > "$TMP_REMOVE"
                    mv "$TMP_REMOVE" "$TASK_FILE"
                    # 追加到 task_abort.json（使用原始任务信息，不含 task_id）
                    if [ ! -f "$ABORT_FILE" ]; then
                        echo "[]" > "$ABORT_FILE"
                    fi
                    TMP_ABORT=$(mktemp)
                    jq ".[] | select(.path == \"$RESP_PATH\" and .tag_content == \"$RESP_TAG\")" "$TASK_FILE" > "$TMP_ABORT" 2>/dev/null || echo "{}" > "$TMP_ABORT"
                    # 如果abort文件是空数组[]
                    if [ ! -s "$TMP_ABORT" ] || [ "$(cat "$TMP_ABORT")" = "[]" ] || [ "$(cat "$TMP_ABORT")" = "" ]; then
                        # 构造一个简化的abort任务对象
                        echo "[{\"path\":\"$RESP_PATH\",\"tag_content\":\"$RESP_TAG\",\"task_time\":\"$(date +%Y-%m-%d\ %H:%M:%S)\"}]" > "$TMP_ABORT"
                    fi
                    jq -n --slurpfile abort "$ABORT_FILE" --slurpfile new "$TMP_ABORT" '$abort[0] + $new[0]' > "$TMP_REMOVE" && mv "$TMP_REMOVE" "$ABORT_FILE"
                    rm -f "$TMP_ABORT"
                fi
            done

            # 清空 response 文件
            echo "[]" > "$REVIEW_RESPONSE_FILE"
        fi

        # 清空 pending 文件
        echo "[]" > "$REVIEW_PENDING_FILE"

        # ==================================================
        # 步骤6：扫描剩余任务中是否还有过期堆积的
        # ==================================================
        echo "🔍 检查是否有新的过期任务..."
        NOW_SEC=$(date +%s)
        TASK_COUNT=$(jq '. | length' "$TASK_FILE" 2>/dev/null || echo 0)
        EXPIRED_COUNT=0

        for (( i=0; i<$TASK_COUNT; i++ )); do
            T_TIME=$(jq -r ".[$i].task_time // empty" "$TASK_FILE")
            [ -z "$T_TIME" ] && break

            T_SEC=$(date -d "$T_TIME" +%s 2>/dev/null)
            if [ -n "$T_SEC" ] && [ "$T_SEC" -lt "$NOW_SEC" ]; then
                EXPIRED_COUNT=$((i+1))
            else
                break
            fi
        done

        if [ "$EXPIRED_COUNT" -gt 0 ]; then
            echo "🗑️ 发现 $EXPIRED_COUNT 个过期任务，移至 task_abort.json..."

            if [ ! -f "$ABORT_FILE" ]; then
                echo "[]" > "$ABORT_FILE"
            fi

            TMP_ABORT=$(mktemp)
            jq --argjson idx "$EXPIRED_COUNT" '.[0:$idx]' "$TASK_FILE" > "$TMP_ABORT"

            TMP_MERGE=$(mktemp)
            jq -s '.[0] + .[1]' "$ABORT_FILE" "$TMP_ABORT" > "$TMP_MERGE"
            mv "$TMP_MERGE" "$ABORT_FILE"

            jq --argjson idx "$EXPIRED_COUNT" '.[$idx:]' "$TASK_FILE" > "$TMP_MERGE" && mv "$TMP_MERGE" "$TASK_FILE"
            rm -f "$TMP_ABORT"
        fi
        # ==================================================

        echo "✅ 本轮处理完成，继续监听..."
        sleep 1
        continue

    else
        # 满足条件：时间还没到（大于 10 分钟） -> 安排“可被打断的休眠”
        echo "⏳ 下一个任务安排在 $TASK_TIME，休眠 $WAIT_SEC 秒..."
        echo "   (如果在休眠期间 task.json 被修改，将立即被打断并重新计算)"
        
        inotifywait -q -t "$WAIT_SEC" -e close_write "$TASK_FILE"
    fi
done
