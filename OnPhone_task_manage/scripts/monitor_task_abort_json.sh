#!/usr/bin/env bash

# ================== 1. 防重复启动锁 ==================
PID_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/abort_monitor.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️ 监控服务已经在后台运行中了 (PID $OLD_PID)，请勿重复启动！"
        exit 1
    fi
fi
echo $$ > "$PID_FILE"

ABORT_FILE="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_abort.json"
DIR_PATH="$(dirname "$ABORT_FILE")"

echo "🚀 task_abort.json 监控服务已启动..."

while true; do
    if [ ! -f "$ABORT_FILE" ]; then
        # 如果文件不存在，监听所在目录的创建或移入事件
        inotifywait -q -e create,moved_to "$DIR_PATH"
        
        # 唤醒后检查是否是我们需要的那个文件被创建了
        if [ -f "$ABORT_FILE" ]; then
            echo "⚡ 检测到 task_abort 创建，暂停监控并开始处理..."
            python ob_task_rearrange.py
            
            # 【核心防抖】：等待2秒，确保 Python 对文件的写入操作彻底落盘结束。
            # 防止自己写入的操作触发下一轮的 inotifywait
            sleep 2 
            echo "✅ 处理完成，恢复监控..."
        fi
    else
        # 如果文件存在，精确监听该文件的写入关闭事件
        inotifywait -q -e close_write "$ABORT_FILE"
        
        echo "⚡ 检测到 task_abort 修改，暂停监控并开始处理..."
        # 统一为你新建的那个挽救任务的脚本
        python ob_task_rearrange.py
        
        # 【核心防抖】：同理，等待落盘冷却
        sleep 2 
        echo "✅ 处理完成，恢复监控..."
    fi
done