#!~/.termux/tasker/md_modifier_task_nohop.sh

# --- 自动后台运行逻辑 ---
if [ "$1" != "--background" ]; then
    # 使用 nohup 启动自身并彻底脱离当前终端会话
    nohup "$0" --background "$@" > /dev/null 2>&1 &
    echo "[*] Obsidian 守护进程已启动并在后台运行 (PID: $!)"
    echo "[*] 启动前同步已开始，请稍候..."
    exit 0
fi

# 移除 --background 内部标记，恢复原始参数
shift 

# --- 配置区 ---
VAULT_NAME="md_db"                           # 你的 Vault 名称
VAULT_PATH="~/storage/shared/MyObsidianVaults/md_db" 
DEFAULT_FILE="base.md"                       # 默认打开的文件

# --- 处理传入参数 ---
TARGET_FILE="${1:-$DEFAULT_FILE}"
ENCODED_FILE=$(echo "$TARGET_FILE" | sed 's/ /%20/g')
URI="obsidian://open?vault=${VAULT_NAME}&file=${ENCODED_FILE}"

# 时间配置
INITIAL_DELAY=1200    # 20 分钟
CHECK_WINDOW=600      # 10 分钟变动检查
RECHECK_DELAY=600     # 循环检查间隔

# --- 正式执行逻辑 ---
cd "$VAULT_PATH" || exit 1

# 1. 【细节添加】打开 Obsidian 之前执行 Git Pull
# 确保你拿到的是服务器上最新的笔记
git pull origin main > /dev/null 2>&1

# 2. 启动 Obsidian
am start -a android.intent.action.VIEW -d "$URI" > /dev/null 2>&1

# 3. 初始静默期（20 分钟内脚本几乎不占 CPU）
sleep "$INITIAL_DELAY"

# 4. 循环监控逻辑
while true; do
    # 检查过去 10 分钟内是否有变动（排除 .git 隐藏目录）
    RECENT_CHANGES=$(find . -type f -not -path '*/.*' -mmin -10)

    if [ -n "$RECENT_CHANGES" ]; then
        # 如果检测到 10 分钟内有改动，则再睡 10 分钟
        sleep "$RECHECK_DELAY"
    else
        # 10 分钟内无变动，说明编辑已停止，开始收尾
        
        # 检查本地是否有需要提交的变更
        if ! git diff-index --quiet HEAD --; then
            git add .
            git commit -m "Auto sync: $TARGET_FILE (System Idle)"
            git push origin main
        fi
        
        # 【细节确认】执行完毕，正常退出进程，释放所有资源
        exit 0
    fi
done
