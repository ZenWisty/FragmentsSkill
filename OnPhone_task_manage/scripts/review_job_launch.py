#!/usr/bin/env python3
import sys
import os
import re
import urllib.parse
import subprocess
from datetime import datetime

# ==========================================
# 1. 解析 Bash 传进来的参数
# ==========================================
if len(sys.argv) < 3:
    print("❌ 参数不足！需要传入 file_path 和 tag_content")
    sys.exit(1)

file_path = sys.argv[1]
tag_content = sys.argv[2]
# sys.argv[3] 是 action (本脚本的名称)，这里不需要用到

if not os.path.exists(file_path):
    print(f"❌ 文件不存在: {file_path}")
    sys.exit(1)

print(f"📖 准备复习笔记: {os.path.basename(file_path)}")

# ==========================================
# 2. 修改 Markdown 文件内容 (追加当前时间)
# ==========================================
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 解析传入的 tag，提取里面的时间内容并追加当前时间
# 注意：本脚本只操作 review: 标签，不触碰 lifepulse: 标签
match = re.search(r'\[##\s*\[review:\s*(.*?)\s*\]\s*##\]', tag_content)
if match:
    inner_times = match.group(1).strip()
    if inner_times:
        new_inner = inner_times + ", " + current_time
    else:
        new_inner = current_time
    new_tag_content = f"[##[review: {new_inner}] ##]"
else:
    # 极低概率正则匹配失败时的兜底
    new_tag_content = tag_content 

line_number = 1
file_modified = False

# 遍历寻找该标签所在的具体行号，并替换文本
for i, line in enumerate(lines):
    if tag_content in line:
        lines[i] = line.replace(tag_content, new_tag_content)
        line_number = i + 1  # 记录行号，供 Obsidian 定位使用
        file_modified = True
        break

if file_modified:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ 文件已更新，打卡时间已记录: {current_time}")
    print("   (后台监控服务将自动计算下一次复习时间并录入 task.json)")
else:
    print("⚠️ 未在文件中找到精确匹配的标签，文本未被修改。")

# ==========================================
# 3. 唤起 Obsidian 并精确定位光标
# ==========================================
# 获取纯文件名，用于在 Obsidian 中搜索/打开
file_name = os.path.basename(file_path)
encoded_file_name = urllib.parse.quote(file_name)
encoded_abs_path = urllib.parse.quote(file_path)

# 【方案 A：精确跳转到具体行 (强烈推荐！)】
# 前提：你必须在 Obsidian 手机端安装第三方插件 `Advanced URI`
uri = f"obsidian://advanced-uri?filepath={encoded_file_name}&line={line_number}"

# 【方案 B：原生打开文件方案 (备用兜底)】
# 如果你没装 Advanced URI 插件，请注释掉上面那行，取消注释下面这行。
# 缺点：只能打开文件，不能自动滚动到标签所在的行。
# uri = f"obsidian://open?path={encoded_abs_path}"

# 使用安卓底层的 am start 唤起 App（测试时设置 REVIEW_TEST_MODE=1 跳过）
if os.getenv("REVIEW_TEST_MODE") != "1":
    command = f'am start -a android.intent.action.VIEW -d "{uri}" > /dev/null 2>&1'
    os.system(command)

print(f"🚀 已唤起 Obsidian，正在定位至第 {line_number} 行...")