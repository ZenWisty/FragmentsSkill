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
ABORT_FILE="$(dirname "$TASK_FILE")/task_abort.json" # 定义 abort 文件的路径

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
        echo "⏰ 距目标时间已不足 10 分钟！开始直接执行目标任务..."
        
        TASK_PATH=$(jq -r '.[0].path // empty' "$TASK_FILE")
        TASK_TAG=$(jq -r '.[0].tag_content // empty' "$TASK_FILE")
        TASK_ACTION=$(jq -r '.[0].action // empty' "$TASK_FILE")
        
        echo "====> 正在调用 review_job_launch.py 处理文件: $TASK_PATH"
        
        # 阻塞调用 Python 脚本
        python review_job_launch.py "$TASK_PATH" "$TASK_TAG" "$TASK_ACTION"

        echo "✅ review_job_launch.py 执行完毕！"

        # 先把刚执行完的第一条正常任务出队
        TMP_FILE=$(mktemp)
        jq '.[1:]' "$TASK_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$TASK_FILE"

        # ==================================================
        # 【新增逻辑】：扫描并剥离已经过期的堆积任务
        # ==================================================
        echo "🔍 正在检查是否有已错失时间的过期任务..."
        NOW_SEC=$(date +%s)
        TASK_COUNT=$(jq '. | length' "$TASK_FILE")
        EXPIRED_COUNT=0
        
        # 从前往后遍历，找到连续过期任务的数量
        for (( i=0; i<$TASK_COUNT; i++ )); do
            T_TIME=$(jq -r ".[$i].task_time // empty" "$TASK_FILE")
            if [ -z "$T_TIME" ]; then break; fi
            
            T_SEC=$(date -d "$T_TIME" +%s 2>/dev/null)
            # 如果解析成功，并且任务设定时间小于当前真实时间，说明已过期
            if[ -n "$T_SEC" ] && [ "$T_SEC" -lt "$NOW_SEC" ]; then
                EXPIRED_COUNT=$((i+1))
            else
                # 由于时间是排序的，只要碰到一个没过期的，后面的绝对没过期，直接打断循环！
                break 
            fi
        done

        if [ "$EXPIRED_COUNT" -gt 0 ]; then
            echo "🗑️ 发现 $EXPIRED_COUNT 个已过期任务，正在移至 task_abort.json..."
            
            # 如果 abort 文件不存在，先初始化一个空数组
            if [ ! -f "$ABORT_FILE" ]; then
                echo "[]" > "$ABORT_FILE"
            fi
            
            # 1. 提取出这些过期的任务
            TMP_ABORT=$(mktemp)
            jq --argjson idx "$EXPIRED_COUNT" '.[0:$idx]' "$TASK_FILE" > "$TMP_ABORT"
            
            # 2. 将它们追加合并到 task_abort.json 的数组中
            TMP_MERGE=$(mktemp)
            jq -s '.[0] + .[1]' "$ABORT_FILE" "$TMP_ABORT" > "$TMP_MERGE"
            mv "$TMP_MERGE" "$ABORT_FILE"
            
            # 3. 将它们从现有的 task.json 中切除掉
            jq --argjson idx "$EXPIRED_COUNT" '.[$idx:]' "$TASK_FILE" > "$TMP_FILE"
            mv "$TMP_FILE" "$TASK_FILE"
            
            rm -f "$TMP_ABORT"
        fi
        # ==================================================
        
        echo "准备拿取现在 task.json 中的(新)第一条信息..."
        sleep 1 # 防抖缓冲
        continue

    else
        # 满足条件：时间还没到（大于 10 分钟） -> 安排“可被打断的休眠”
        echo "⏳ 下一个任务安排在 $TASK_TIME，休眠 $WAIT_SEC 秒..."
        echo "   (如果在休眠期间 task.json 被修改，将立即被打断并重新计算)"
        
        inotifywait -q -t "$WAIT_SEC" -e close_write "$TASK_FILE"
    fi
done
