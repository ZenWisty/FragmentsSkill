#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime, timedelta

# ==========================================
# 1. 配置区域
# ==========================================
if len(sys.argv) < 2:
    print("❌ 错误: 未传入被修改的 .md 文件路径！")
    sys.exit(1)

MD_PATH = sys.argv[1]
TASK_JSON_PATH = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task.json"
LONGTERM_JSON_PATH = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_longterm.json"
ACTION_SCRIPT = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts/review_job_launch.py"

# 休息时间范围：每天 23:30 → 次日 07:45
REST_START_HOUR = 23
REST_START_MIN = 30
REST_END_HOUR = 7
REST_END_MIN = 45


def rest_time_skip(dt):
    """
    如果 dt 落在休息时间段（23:30 → 次日 07:45），则顺延到 07:45。
    否则原样返回。
    """
    hour, minute = dt.hour, dt.minute
    # 当天 23:30 之后 → 视为休息开始
    if hour > REST_START_HOUR or (hour == REST_START_HOUR and minute >= REST_START_MIN):
        # 顺延到次日 07:45
        return dt.replace(hour=REST_END_HOUR, minute=REST_END_MIN, second=0, microsecond=0) + timedelta(days=1)
    # 次日 00:00 ~ 07:45 之前 → 也在休息中
    if hour < REST_END_HOUR or (hour == REST_END_HOUR and minute < REST_END_MIN):
        return dt.replace(hour=REST_END_HOUR, minute=REST_END_MIN, second=0, microsecond=0)
    return dt


def func1(past_times):
    """
    根据过去的复习时间列表，计算并返回下一次复习的时间。
    复习间隔表：
      0 次历史 → 现在 + 20 分钟
      1 次历史 → 第1次复习 + 12 小时
      2 次历史 → 第2次复习 + 6 天
      3 次历史 → 第3次复习 + 10 天
      4 次历史 → 第4次复习 + 3 个月（之后结束，不再安排）
    """
    count = len(past_times)

    if count == 0:
        next_time = datetime.now() + timedelta(minutes=20)
    elif count == 1:
        t = datetime.strptime(past_times[0], "%Y-%m-%d %H:%M:%S")
        next_time = t + timedelta(hours=12)
    elif count == 2:
        t = datetime.strptime(past_times[1], "%Y-%m-%d %H:%M:%S")
        next_time = t + timedelta(days=6)
    elif count == 3:
        t = datetime.strptime(past_times[2], "%Y-%m-%d %H:%M:%S")
        next_time = t + timedelta(days=10)
    elif count == 4:
        t = datetime.strptime(past_times[3], "%Y-%m-%d %H:%M:%S")
        next_time = t + timedelta(days=90)  # 3 个月 ≈ 90 天
    else:
        # 5 次及以上，不再安排
        return None

    # 休息时间顺延
    next_time = rest_time_skip(next_time)
    return next_time.strftime("%Y-%m-%d %H:%M:%S")


# ==========================================
# 2. 读取原始数据并做防冲突清理
# ==========================================
if os.path.exists(TASK_JSON_PATH):
    try:
        with open(TASK_JSON_PATH, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except json.JSONDecodeError:
        tasks = []
else:
    tasks = []

old_tasks_str = json.dumps(tasks, sort_keys=True)

# 🌟 幂等性清理：剔除掉现存 task.json 中所有属于当前 .md 文件的旧任务
tasks = [t for t in tasks if t.get('path') != MD_PATH]

# ── 读取并清理 longterm 中该文件的旧任务 ───────────────────────
if os.path.exists(LONGTERM_JSON_PATH):
    try:
        with open(LONGTERM_JSON_PATH, 'r', encoding='utf-8') as f:
            longterm_tasks = json.load(f)
    except json.JSONDecodeError:
        longterm_tasks = []
else:
    longterm_tasks = []

longterm_tasks = [t for t in longterm_tasks if t.get('path') != MD_PATH]
old_longterm_str = json.dumps(longterm_tasks, sort_keys=True)

# ==========================================
# 3. 扫描 Markdown，提取 review 标签
# ==========================================
if not os.path.exists(MD_PATH):
    print(f"⚠️ 文件不存在或已被删除: {MD_PATH}")
    sys.exit(0)

with open(MD_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

# ── 解析 review 标签 ────────────────────────────────────────────
# review: 逗号分隔的历史时间列表
REVIEW_PATTERN = r'\[##\s*\[review:\s*(.*?)\s*\]\s*##\]'

new_tasks_for_this_file = []
limit_time_obj = datetime.now() + timedelta(days=7)

for match in re.finditer(REVIEW_PATTERN, md_content):
    full_tag_str = match.group(0)
    times_str = match.group(1)

    if times_str and times_str.strip():
        past_times = [t.strip() for t in times_str.split(',') if t.strip()]
    else:
        past_times = []

    # 调用算法计算下一次复习时间
    next_time_str = func1(past_times)

    if not next_time_str:
        continue

    next_time_obj = datetime.strptime(next_time_str, "%Y-%m-%d %H:%M:%S")
    task_entry = {
        "task_time": next_time_str,
        "path": MD_PATH,
        "tag_content": full_tag_str,
        "action": ACTION_SCRIPT
    }

    if next_time_obj <= limit_time_obj:
        # 7 天内 → 进入 task.json
        new_tasks_for_this_file.append(task_entry)
    else:
        # 超过 7 天 → 进入 longterm 队列
        longterm_tasks.append(task_entry)

# ==========================================
# 4. 合并、排序与脏写入检测
# ==========================================
tasks.extend(new_tasks_for_this_file)
tasks.sort(key=lambda x: x['task_time'])
longterm_tasks.sort(key=lambda x: x['task_time'])

new_tasks_str = json.dumps(tasks, sort_keys=True)
new_longterm_str = json.dumps(longterm_tasks, sort_keys=True)

if new_tasks_str != old_tasks_str:
    with open(TASK_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f"✅ task.json 已更新并排序: {os.path.basename(MD_PATH)} (新增有效任务 {len(new_tasks_for_this_file)} 个)")
else:
    print(f"💤 task.json 无实质变动。")

if new_longterm_str != old_longterm_str:
    with open(LONGTERM_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(longterm_tasks, f, indent=2, ensure_ascii=False)
    print(f"✅ task_longterm.json 已更新并排序 (共 {len(longterm_tasks)} 个长期任务)")
else:
    print(f"💤 task_longterm.json 无实质变动。")
