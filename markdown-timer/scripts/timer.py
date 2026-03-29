import json
import os
import time
import threading
from datetime import datetime, timedelta
from filelock import FileLock
from apscheduler.schedulers.blocking import BlockingScheduler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 配置与路径 ---
CONFIG_DIR = os.path.expanduser("~/.config/claude_manager/")
TASK_FILE = os.path.join(CONFIG_DIR, "tasks.json")
EXPIRED_FILE = os.path.join(CONFIG_DIR, "expired_tasks.json")
LOCK_FILE = os.path.join(CONFIG_DIR, "tasks.json.lock")

# 全局运行锁：确保只有一个执行器在运行
execution_lock = threading.Lock()
# 标志位：防止定时器修改文件时触发自己的 inotify
is_internal_modifying = False

# --- 预留接口 (Interfaces) ---

def review_executor(task):
    """
    复习执行器接口
    逻辑：处理单条任务。由于执行时间可能较长，定时器在此期间保持唤醒。
    """
    print(f">>> [执行器] 开始处理任务: {task['file']} 内容: {task['content'][:20]}...")
    # TODO: 以后在此处集成 Claude API 或通知逻辑
    
    time.sleep(2) # 模拟耗时操作
    print(">>> [执行器] 任务执行完毕。")

def schedule_parser():
    """解析器接口：扫描文档并更新 task.json"""
    pass

def doc_editor():
    """文档编辑器接口：手动或自动修改文档内容"""
    pass

# --- 工具函数 ---

def safe_io(action, data=None):
    """带锁的 JSON 读写"""
    global is_internal_modifying
    lock = FileLock(LOCK_FILE)
    with lock:
        if action == "read":
            if not os.path.exists(TASK_FILE): return {"tasks": []}
            with open(TASK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif action == "write":
            is_internal_modifying = True  # 标记为内部修改
            try:
                with open(TASK_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            finally:
                # 延迟重置，确保 inotify 事件已经产生并被过滤
                time.sleep(0.1)
                is_internal_modifying = False

def archive_expired(task):
    """将过期任务写入独立文档"""
    lock = FileLock(LOCK_FILE)
    with lock:
        expired_data = []
        if os.path.exists(EXPIRED_FILE):
            with open(EXPIRED_FILE, 'r', encoding='utf-8') as f:
                expired_data = json.load(f)
        expired_data.append(task)
        with open(EXPIRED_FILE, 'w', encoding='utf-8') as f:
            json.dump(expired_data, f, indent=4, ensure_ascii=False)

# --- 定时器核心逻辑 ---

def timer_main_logic():
    """定时器的主要唤醒逻辑"""
    if not execution_lock.acquire(blocking=False):
        print("[定时器] 执行器正在运行，跳过本次唤醒。")
        return

    try:
        data = safe_io("read")
        tasks = data.get("tasks", [])
        if not tasks:
            reschedule(datetime.now() + timedelta(hours=1))
            return

        now = datetime.now()
        # 始终检查首条任务
        first_task = tasks[0]
        task_time = datetime.fromisoformat(first_task['time'])

        # 检查是否在当前时间前后 5 分钟内
        if abs((task_time - now).total_seconds()) <= 300:
            # 调用复习执行器
            review_executor(first_task)
            
            # 执行结束后：删除该任务并清理所有过期任务
            data = safe_io("read") # 重新读取以防执行期间文件变动
            current_tasks = data.get("tasks", [])
            
            remaining_tasks = []
            for t in current_tasks:
                t_time = datetime.fromisoformat(t['time'])
                # 如果任务是刚执行的那条，或者是已经过期超过5分钟的
                if (t['file'] == first_task['file'] and t['content'] == first_task['content']) or (t_time < now - timedelta(minutes=5)):
                    archive_expired(t)
                else:
                    remaining_tasks.append(t)
            
            safe_io("write", {"tasks": remaining_tasks})
            
            # 递归：处理完后立即检查下一条，防止堆积
            execution_lock.release() # 先释放锁以便递归调用能重新获取
            timer_main_logic()
            return
        
        else:
            # 不在执行窗口内，安排下一次唤醒
            reschedule(task_time)

    finally:
        if execution_lock.locked():
            execution_lock.release()

def reschedule(run_time):
    scheduler.remove_all_jobs()
    scheduler.add_job(timer_main_logic, 'date', run_date=run_time)
    print(f"[状态] 沉睡中。下次计划唤醒: {run_time.strftime('%H:%M:%S')}")

# --- Inotify 监控 ---

class TaskWatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == TASK_FILE:
            if is_internal_modifying:
                # 过滤掉定时器自己修改文件引发的事件
                return
            print("[Inotify] 检测到外部修改，唤醒定时器...")
            timer_main_logic()

# --- 启动 ---
scheduler = BlockingScheduler()

if __name__ == "__main__":
    if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
    
    observer = Observer()
    observer.schedule(TaskWatchHandler(), CONFIG_DIR, recursive=False)
    observer.start()

    print("Claude 智能调度系统 V2 已启动...")
    timer_main_logic() # 初始检查

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        observer.stop()
    observer.join()
