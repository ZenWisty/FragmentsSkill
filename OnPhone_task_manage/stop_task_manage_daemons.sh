#!/usr/bin/env bash
#
# 停止所有后台 daemon 脚本
# 用法: bash stop_task_manage_daemons.sh
#
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs"

echo "=========================================="
echo "  Obsidian 任务调度系统停止脚本"
echo "=========================================="

# PID 文件列表
PID_FILES=(
    "$DOCS_DIR/vault_monitor.pid"
    "$DOCS_DIR/task_runner.pid"
    "$DOCS_DIR/abort_monitor.pid"
    "$DOCS_DIR/longterm_poll.pid"
)

stop_by_pidfile() {
    local pidfile=$1
    local name=$(basename "$pidfile" .pid)

    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 停止 $name (PID=$PID) ..."
            kill "$PID" 2>/dev/null
            # 等待进程退出
            for i in $(seq 1 5); do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 0.5
            done
            # 如果还在跑，强制杀掉
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null
            fi
            echo "   ✅ $name 已停止"
        else
            echo "   ℹ️  $name 未在运行（残留PID文件已清理）"
        fi
        rm -f "$pidfile"
    else
        echo "   ℹ️  $name 无PID文件（可能未启动）"
    fi
}

echo ""
for pidfile in "${PID_FILES[@]}"; do
    stop_by_pidfile "$pidfile"
done

echo ""
echo "=========================================="
echo "  全部停止完成"
echo "=========================================="
