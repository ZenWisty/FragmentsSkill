#!/data/data/com.termux/files/usr/bin/bash

# --- 配置区 ---
VAULT_NAME="md_db"
VAULT_PATH="$HOME/storage/shared/MyObsidianVaults/md_db"
DEFAULT_FILE="base.md"

# --- 参数处理 ---
# $1: 文件路径 (默认为 base.md)
# $2: 行号 (数字)
TARGET_FILE="${1:-$DEFAULT_FILE}"
LINE_NUM="$2"

# URL 编码函数（处理路径中的空格）
urlencode() {
    echo "$1" | sed 's/ /%20/g'
}

ENCODED_FILE=$(urlencode "$TARGET_FILE")

# --- 构建 URI ---
if [ -n "$LINE_NUM" ]; then
    # 如果指定了行号，使用 Advanced URI 插件协议
    # 注意：这需要你在 Obsidian 中安装 "Advanced URI" 插件
    URI="obsidian://advanced-uri?vault=${VAULT_NAME}&filepath=${ENCODED_FILE}&line=${LINE_NUM}"
else
    # 如果没指定行号，使用官方标准协议打开文件
    URI="obsidian://open?vault=${VAULT_NAME}&file=${ENCODED_FILE}"
fi

# --- 执行跳转 ---
if [ ! -d "$VAULT_PATH" ]; then
    echo "警告: 库路径不存在 $VAULT_PATH"
fi

echo "[*] 正在打开: $TARGET_FILE ${LINE_NUM:+在第 }$LINE_NUM 行"

# 发送 Intent 唤起 Obsidian
am start -a android.intent.action.VIEW -d "$URI" > /dev/null 2>&1

exit 0
