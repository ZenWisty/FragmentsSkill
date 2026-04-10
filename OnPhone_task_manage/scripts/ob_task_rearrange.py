#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# ==========================================
# 1. 基础配置
# ==========================================
TASK_JSON_PATH = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task.json"
ABORT_JSON_PATH = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/task_abort.json"
GAP_MINUTES = 15  # 任务之间的最小时间间隔（分钟）

def find_next_available_slot(start_time, occupied_times, min_gap_minutes):
    """
    碰撞检测算法：从 start_time 开始向后寻找空档，
    确保找出的时间点与 occupied_times 中任何一个时间的绝对差值 >= min_gap_minutes。
    """
    candidate = start_time
    gap = timedelta(minutes=min_gap_minutes)
    
    while True:
        conflict = False
        for occ in occupied_times:
            # 如果候选时间与已占用时间的距离小于规定的间隔，则发生碰撞
            if abs((candidate - occ).total_seconds()) < gap.total_seconds():
                conflict = True
                # 发生碰撞后，直接把候选时间推延到该占用时间之后的 15 分钟，然后重新检测全部
                candidate = occ + gap
                break
        
        # 如果遍历完所有已占用时间都没有发生碰撞，说明找到了完美空隙！
        if not conflict:
            return candidate

def main():
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)

    # ==========================================
    # 2. 读取并筛选 task_abort.json
    # ==========================================
    if not os.path.exists(ABORT_JSON_PATH):
        print("💤 task_abort.json 不存在，无需安排。")
        return

    with open(ABORT_JSON_PATH, 'r', encoding='utf-8') as f:
        try:
            abort_tasks = json.load(f)
        except json.JSONDecodeError:
            abort_tasks =[]

    if not abort_tasks:
        print("💤 task_abort.json 为空，无需安排。")
        return

    tasks_to_reschedule = []
    remaining_abort_tasks =[]

    # 过滤出 2 小时内过期的任务
    for task in abort_tasks:
        try:
            t_obj = datetime.strptime(task['task_time'], "%Y-%m-%d %H:%M:%S")
            # 判断过期时间是否在过去的 2 小时以内
            if two_hours_ago <= t_obj <= now:
                tasks_to_reschedule.append(task)
            else:
                remaining_abort_tasks.append(task)
        except (ValueError, KeyError):
            # 时间格式错误的脏数据，继续留在 abort 里
            remaining_abort_tasks.append(task)

    if not tasks_to_reschedule:
        print("💤 没有发现2小时内过期的任务需要重新安排。")
        return

    # 按照原本的时间先后顺序排个序，保证早过期的早安排
    tasks_to_reschedule.sort(key=lambda x: x.get('task_time', ""))

    # ==========================================
    # 3. 读取 task.json 并获取所有已占用时间点
    # ==========================================
    if os.path.exists(TASK_JSON_PATH):
        with open(TASK_JSON_PATH, 'r', encoding='utf-8') as f:
            try:
                active_tasks = json.load(f)
            except json.JSONDecodeError:
                active_tasks = []
    else:
        active_tasks =[]

    occupied_times =[]
    for task in active_tasks:
        try:
            t_obj = datetime.strptime(task['task_time'], "%Y-%m-%d %H:%M:%S")
            occupied_times.append(t_obj)
        except (ValueError, KeyError):
            pass
    
    occupied_times.sort()

    # ==========================================
    # 4. 核心：为过期任务安插新时间
    # ==========================================
    print(f"🔄 准备将 {len(tasks_to_reschedule)} 个过期任务重新安插回时间线...")
    
    for task in tasks_to_reschedule:
        # 从"现在"开始往后寻找缝隙
        new_time = find_next_available_slot(now, occupied_times, GAP_MINUTES)
        
        # 赋予新时间
        task['task_time'] = new_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 将安排好的任务加入队列
        active_tasks.append(task)
        
        # 把这个新时间也登记到“已占用”列表里，确保下一个安插的任务不会和它撞车
        occupied_times.append(new_time)
        occupied_times.sort()

    # ==========================================
    # 5. 更新写入两个 JSON 文件
    # ==========================================
    # 将 task.json 重新按时间从小到大排序
    active_tasks.sort(key=lambda x: x['task_time'])

    with open(TASK_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(active_tasks, f, indent=2, ensure_ascii=False)

    with open(ABORT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(remaining_abort_tasks, f, indent=2, ensure_ascii=False)

    print(f"✅ 安排完成！成功救回 {len(tasks_to_reschedule)} 个任务，已写入 task.json。")

if __name__ == "__main__":
    main()