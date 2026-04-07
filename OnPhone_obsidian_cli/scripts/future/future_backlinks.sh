#!/bin/bash
# obsidian_cli.sh - 完整的 Obsidian CLI 工具

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_PATH="${OBSIDIAN_VAULT:-/storage/emulated/0/Documents/Obsidian Vault}"
PYTHON_SCRIPT="$SCRIPT_DIR/get_backlinks_full.py"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Obsidian Vault CLI (Python 版)"
    echo ""
    echo "用法:"
    echo "  $0 backlinks <文件路径> [--check]    获取文件的 backlinks"
    echo "  $0 stats                              统计 Vault 信息"
    echo "  $0 check <文件路径>                   检查 backlink 有效性"
    echo ""
    echo "环境变量:"
    echo "  OBSIDIAN_VAULT    设置 Vault 路径"
    echo ""
    echo "示例:"
    echo "  $0 backlinks \"工具整理/手机 android harmony 配置.md\""
    echo "  $0 backlinks \"工具整理/手机 android harmony 配置.md\" --check"
}

resolve_path() {
    local input_path="$1"
    if [[ "$input_path" == /* ]]; then
        echo "$input_path"
    else
        echo "$VAULT_PATH/$input_path"
    fi
}

cmd_backlinks() {
    local file="$1"
    shift  # 移除第一个参数，剩下的传给 python
    
    if [ -z "$file" ]; then
        echo -e "${RED}错误: 请提供文件路径${NC}"
        usage
        exit 1
    fi
    
    local full_path
    full_path=$(resolve_path "$file")
    
    if [ ! -f "$full_path" ]; then
        echo -e "${RED}错误: 文件不存在: $full_path${NC}"
        exit 1
    fi
    
    # 转换为相对路径（相对于 vault）
    local rel_path="${full_path#$VAULT_PATH/}"
    
    # 调用 Python 脚本
    python3 "$PYTHON_SCRIPT" "$rel_path" --vault "$VAULT_PATH" "$@"
}

cmd_stats() {
    echo "Vault 路径: $VAULT_PATH"
    echo "文件总数: $(find "$VAULT_PATH" -name "*.md" | wc -l)"
    echo "Python 脚本: $PYTHON_SCRIPT"
}

# 主命令分发
case "${1:-}" in
    backlinks)
        shift
        cmd_backlinks "$@"
        ;;
    stats)
        cmd_stats
        ;;
    check)
        shift
        cmd_backlinks "$@" --check
        ;;
    --help|-h|help)
        usage
        ;;
    *)
        echo -e "${RED}未知命令: ${1:-}${NC}"
        usage
        exit 1
        ;;
esac

# 使用示例：
# 1. 基础用法: 获取 backlinks 列表
$ ./obsidian_cli.sh backlinks "工具整理/手机 android harmony 配置.md"
工具整理/自动化复习规划提示 代理/obsidian 细节 使用.md
工具整理/自动化复习规划提示 代理/自动化 复习 规划 提示 代理.md

# 2. 验证模式: 检查哪些 backlink 文件存在
$ ./obsidian_cli.sh check "工具整理/手机 android harmony 配置.md"
📄 文件: /storage/emulated/0/Documents/Obsidian Vault/工具整理/手机 android harmony 配置.md
📝 标题: 手机 Android Harmony 配置
🔗 Backlinks 总数: 2
✅ 有效链接: 2
❌ 死链: 0

有效链接:
  ✓ 工具整理/自动化复习规划提示 代理/obsidian 细节 使用.md
  ✓ 工具整理/自动化复习规划提示 代理/自动化 复习 规划 提示 代理.md

# 3. JSON 输出（用于其他程序处理）
$ ./obsidian_cli.sh backlinks "工具整理/手机 android harmony 配置.md" --json
{
  "file": "工具整理/手机 android harmony 配置.md",
  "title": "手机 Android Harmony 配置",
  "backlinks": [
    "工具整理/自动化复习规划提示 代理/obsidian 细节 使用.md",
    "工具整理/自动化复习规划提示 代理/自动化 复习 规划 提示 代理.md"
  ],
  "count": 2,
  "valid_count": 2
} 





# 标准 osidian cli 返回
obsidian backlinks path="工具整理/自动化复习规划提示 代理/本地知识库/单词.md" format=json

[
  {
    "file": "工具整理/自动化复习规划提示 代理/本地知识库/本地知识库.md"
  }
]