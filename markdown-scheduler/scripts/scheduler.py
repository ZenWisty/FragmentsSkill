import json
import re
import os
import time
from datetime import datetime, timedelta
from filelock import FileLock
from apscheduler.schedulers.blocking import BlockingScheduler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import parser_c

# --- 配置 ---
CONFIG_DIR = os.path.expanduser("~/.config/ai_scheduler/")
TASK_FILE = os.path.join(CONFIG_DIR, "tasks.json")
ARCHIVE_FILE = os.path.join(CONFIG_DIR, "archive.json")
LOCK_FILE = os.path.join(CONFIG_DIR, "tasks.json.lock")

# 需要扫描的 Markdown 文件所在目录或列表
MD_FILES = [os.path.expanduser("~/notes/example.md")] 

# --- 工具函数 ---

def safe_load_json(file_path):
    """带锁安全读取"""
    lock = FileLock(LOCK_FILE)
    with lock:
        if not os.path.exists(file_path):
            return {"tasks": []} if "tasks" in file_path else []
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"tasks": []}

def safe_save_json(file_path, data):
    """带锁安全写入"""
    lock = FileLock(LOCK_FILE)
    with lock:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def custom_schedule_logic(time_list):
    """从时间列表中计算下一个有效时间（未来最近的时间）"""
    now = datetime.now()
    future_times = []
    for t_str in time_list:
        try:
            t_dt = datetime.fromisoformat(t_str)
            if t_dt > now:
                future_times.append(t_dt)
        except ValueError:
            continue
    return min(future_times) if future_times else None

# --- 核心逻辑：扫描与同步 ---

def scan_and_sync():
    """扫描 MD 文件并同步到 JSON (核心逻辑已封装)"""
    print(f"[{datetime.now()}] 启动安全扫描...")
    
    # 调用封装好的二进制接口
    # 传入文件列表和之前定义的时间计算逻辑函数
    found_tasks = parser_c.parse_markdown_files(MD_FILES, custom_schedule_logic)

    # --- 以下保持原有的写入 JSON 逻辑 ---
    current_data = safe_load_json(TASK_FILE)
    active_tasks = current_data.get("tasks", [])
    
    seen = set()
    final_active = []
    # 合并、去重、排序
    for t in (found_tasks + active_tasks):
        # 确保一周内的过滤逻辑（如果 parser_core 没做，这里做）
        t_time = datetime.fromisoformat(t['time'])
        if t_time > datetime.now() + timedelta(days=7):
            continue
            
        uid = f"{t['file']}_{t['id']}_{t['time']}"
        if uid not in seen:
            final_active.append(t)
            seen.add(uid)
            
    final_active.sort(key=lambda x: x['time'])
    safe_save_json(TASK_FILE, {"tasks": final_active})
    return final_active

# --- 调度与唤醒逻辑 ---

class ConfigFolderHandler(FileSystemEventHandler):
    """inotify 监听：当外部程序修改 tasks.json 时，强制调度器重新计算"""
    def __init__(self, callback):
        self.callback = callback
    def on_modified(self, event):
        if event.src_path.endswith("tasks.json"):
            print("检测到 tasks.json 外部变动，唤醒调度器...")
            self.callback()

def job_wrapper():
    """主调度循环"""
    # 1. 执行扫描同步
    active_tasks = scan_and_sync()
    
    # 2. 检查是否有任务到期
    if active_tasks:
        now = datetime.now()
        first_task = active_tasks[0]
        task_time = datetime.fromisoformat(first_task['time'])
        
        if now >= task_time - timedelta(seconds=2):
            print(f"!!! 任务到期触发 !!! ID: {first_task['id']}, 文件: {first_task['file']}")
            
            # --- 此处预留 trigger_claude_skill 调用接口 ---
            # pass 
            
            # 3. 归档已完成任务
            completed_task = active_tasks.pop(0)
            archive_data = safe_load_json(ARCHIVE_FILE)
            archive_data.append(completed_task)
            safe_save_json(ARCHIVE_FILE, archive_data)
            
            # 更新活跃任务表
            safe_save_json(TASK_FILE, {"tasks": active_tasks})
            
            # 立即再次检查下一个任务
            return job_wrapper()

        # 4. 安排下一次定时唤醒
        reschedule(task_time)
    else:
        # 如果当前无任务，1小时后唤醒进行例行扫描
        reschedule(datetime.now() + timedelta(hours=1))

def reschedule(run_time):
    scheduler.remove_all_jobs()
    scheduler.add_job(job_wrapper, 'date', run_date=run_time)
    print(f"进入休眠。下次唤醒时间: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")

scheduler = BlockingScheduler()

if __name__ == "__main__":
    # 启动文件监控 (inotify)
    observer = Observer()
    handler = ConfigFolderHandler(job_wrapper)
    observer.schedule(handler, CONFIG_DIR, recursive=False)
    observer.start()

    print("Claude 后台调度服务已启动...")
    # 初始执行
    scheduler.add_job(job_wrapper, 'date', run_date=datetime.now())
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        observer.stop()
    observer.join()
