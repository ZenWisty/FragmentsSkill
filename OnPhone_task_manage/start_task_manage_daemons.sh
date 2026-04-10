#!/usr/bin/env bash
#
# 启动所有后台 daemon 脚本
# 用法: bash start_task_manage_daemons.sh
#
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  Obsidian 任务调度系统启动脚本"
echo "=========================================="

# 检查依赖
for cmd in jq inotifywait date flock; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ 缺少依赖: $cmd"
        exit 1
    fi
done
echo "✅ 依赖检查通过"

# 检查 lock 文件（简单粗暴检测是否有 daemon 在跑）
LOCKS=(
    "$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_runner.lock"
    "$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/abort_monitor.lock"
    "$HOME/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/longterm_poll.lock"
)

for lock in "${LOCKS[@]}"; do
    if [ -f "$lock" ]; then
        # 检查锁是否被占用（flock -n 失败说明有进程持锁）
        if ! flock -n 200 "$lock" 200>/dev/null 2>&1; then
            echo "⚠️  检测到已有实例运行: $lock"
        fi
    fi
done

echo ""
echo "启动顺序："
echo "  1. polling_manage_longterm_task.sh  (每日23:40轮询)"
echo "  2. monitor_task_json.sh            (任务调度，10分钟窗口)"
echo "  3. monitor_task_abort_json.sh      (abort监控)"
echo "  4. monitor_vault_md.sh             (vault文件监控)"
echo ""

# 启动函数
start_daemon() {
    local name=$1
    local script=$2
    local log="$SCRIPT_DIR/../docs/logs/${name}.log"
    mkdir -p "$(dirname "$log")"
    echo "🚀 启动 $name ..."
    nohup bash "$script" >> "$log" 2>&1 &
    echo "   PID=$! log=$log"
}

# 逐个启动（polling 放第一位，因为其他三个是事件驱动的）
start_daemon "polling_manage_longterm_task" "$SCRIPT_DIR/polling_manage_longterm_task.sh"
start_daemon "monitor_task_json"           "$SCRIPT_DIR/monitor_task_json.sh"
start_daemon "monitor_task_abort_json"     "$SCRIPT_DIR/monitor_task_abort_json.sh"
start_daemon "monitor_vault_md"            "$SCRIPT_DIR/monitor_vault_md.sh"

echo ""
echo "=========================================="
echo "  全部启动完成"
echo "  查看日志: ls ../docs/logs/"
echo "  停止所有: pkill -f 'monitor_|polling_'"
echo "=========================================="
