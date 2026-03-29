import os
import json
import sys
import fcntl
from datetime import datetime, timedelta
from filelock import FileLock

# 导入已编译的二进制模块
import Ebbinghaus 
import parser_core

# --- 配置 ---
CONFIG_DIR = os.path.expanduser("~/.config/claude_manager/")
TASK_FILE = os.path.join(CONFIG_DIR, "tasks.json")
LOCK_FILE = os.path.join(CONFIG_DIR, "tasks.json.lock")
# 进程锁文件，确保同一时间只有一个修改器在运行
INSTANCE_LOCK = os.path.join(CONFIG_DIR, "modifier.instance.lock")

def doc_editor_replace(file_path, old_content, new_content):
    """【文档编辑器接口】执行 Step 3 的回写逻辑"""
    if not old_content or old_content == new_content:
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        if old_content in full_text:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_text.replace(old_content, new_content))
            print(f"[编辑器] 已更新文件: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"[编辑器错误] 无法更新 {file_path}: {e}")

def process_tasks(incoming_pairs=None):
    """
    核心修改逻辑
    incoming_pairs 格式: [(标签内容, 文件路径), ...]
    """
    # Step 4: 文件系统级排他锁，防止多进程冲突
    lock_fd = open(INSTANCE_LOCK, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Error: Another task_modifier instance is already running.")
        return

    # 使用 FileLock 保护 JSON 文件读写
    json_lock = FileLock(LOCK_FILE)
    with json_lock:
        # 加载现有任务
        if os.path.exists(TASK_FILE):
            with open(TASK_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {"tasks": []}
        else:
            data = {"tasks": []}
        
        current_tasks = data.get("tasks", [])
        has_changes = False

        # --- Step 1 & 3: 处理传入的新标签 ---
        if incoming_pairs:
            for tag_content, file_path in incoming_pairs:
                # Step 3: 调用艾宾浩斯接口计算下一次时间并更新标签
                # 返回 (next_time_dt, updated_tag_content)
                next_time, updated_tag = Ebbinghaus.curve_api(tag_content)
                
                # 过滤：仅保留一周内的任务
                if next_time and next_time <= datetime.now() + timedelta(days=7):
                    # 同步回写到 .md 文档
                    doc_editor_replace(file_path, tag_content, updated_tag)
                    
                    # 放入待写入 JSON 的列表
                    current_tasks.append({
                        "time": next_time.isoformat(),
                        "file": file_path,
                        "content": updated_tag
                    })
                    has_changes = True

        # --- Step 2: 扫描并调整任务密度 (2小时内) ---
        if current_tasks:
            now = datetime.now()
            two_hours_limit = now + timedelta(hours=2)
            
            # 找到 2 小时内的索引
            near_indices = [
                i for i, t in enumerate(current_tasks) 
                if now <= datetime.fromisoformat(t['time']) <= two_hours_limit
            ]
            
            if near_indices:
                near_contents = [current_tasks[i]['content'] for i in near_indices]
                # 调用 Ebbinghaus 挤压密度逻辑
                adjusted_results = Ebbinghaus.adjust_current_task(near_contents)
                
                # 检查并更新变动
                for i, idx in enumerate(near_indices):
                    # 假设返回结果包含 {'time': '...', 'content': '...'}
                    if current_tasks[idx]['time'] != adjusted_results[i]['time']:
                        current_tasks[idx]['time'] = adjusted_results[i]['time']
                        current_tasks[idx]['content'] = adjusted_results[i]['content']
                        has_changes = True

        # --- 最终同步：排序与去重 ---
        if has_changes or incoming_pairs:
            # 去重依据：文件路径 + 标签内容
            unique_map = {}
            for t in current_tasks:
                key = f"{t['file']}_{t['content']}"
                # 如果有重复，保留时间更近的（或根据需求覆盖）
                unique_map[key] = t
            
            # 排序
            sorted_tasks = sorted(unique_map.values(), key=lambda x: x['time'])
            
            with open(TASK_FILE, 'w', encoding='utf-8') as f:
                json.dump({"tasks": sorted_tasks}, f, indent=4, ensure_ascii=False)
            print(f"Success: {len(sorted_tasks)} tasks sorted and saved.")
        else:
            print("no task change")

if __name__ == "__main__":
    # 支持命令行 JSON 输入，方便外部程序调用
    # 示例用法: python task_modifier.py '[["[##标签##]", "/path/to/a.md"]]'
    if len(sys.argv) > 1:
        try:
            raw_input = json.loads(sys.argv[1])
            process_tasks(raw_input)
        except Exception as e:
            print(f"Input Error: {e}")
    else:
        # 如果没有传入参数，仅执行 Step 2 的密度检查
        process_tasks()
