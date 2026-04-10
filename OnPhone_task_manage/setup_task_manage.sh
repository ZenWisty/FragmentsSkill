#!/usr/bin/env bash
#
# 将启动/停止脚本安装到 Termux ~/.shortcuts/ 目录
# 运行一次即可：bash setup_task_manage.sh
#
mkdir -p "$HOME/.shortcuts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 启动脚本
cat > "$HOME/.shortcuts/start_task_manage_daemons.sh" << 'EOF'
#!/usr/bin/env bash
bash /storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/start_task_manage_daemons.sh
EOF
chmod +x "$HOME/.shortcuts/start_task_manage_daemons.sh"
echo "✅ 启动脚本已安装到 ~/.shortcuts/start_task_manage_daemons.sh"

# 停止脚本
cat > "$HOME/.shortcuts/stop_task_manage_daemons.sh" << 'EOF'
#!/usr/bin/env bash
bash /storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/stop_task_manage_daemons.sh
EOF
chmod +x "$HOME/.shortcuts/stop_task_manage_daemons.sh"
echo "✅ 停止脚本已安装到 ~/.shortcuts/stop_task_manage_daemons.sh"
