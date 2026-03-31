#!/bin/bash
# --- 配置文件名 ---
VAULT_NAME="md_db"  # 确保这个名字和你在 Obsidian App 里建立的库名一致
FILE_NAME=$1

# 如果输入包含路径，只提取相对于库根目录的部分
# 比如输入 "test/note.md"，Obsidian URI 只需要 "test/note.md"
CLEAN_FILE=$(basename "$FILE_NAME")

# 调用安卓 Activity Manager 唤起 Obsidian
# 注意：这里直接唤起 URI 协议
am start -a android.intent.action.VIEW \
   -d "obsidian://open?vault=${VAULT_NAME}&file=${CLEAN_FILE}" > /dev/null 2>&1

echo "正在 Obsidian 中打开: $CLEAN_FILE"
