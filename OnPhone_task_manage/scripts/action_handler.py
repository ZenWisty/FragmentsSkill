#!/usr/bin/env python3
import sys, json, time, os

DOCS_DIR = "/data/data/com.termux/files/home/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs"
PENDING_FILE = os.path.join(DOCS_DIR, "review_pending.json")
RESPONSE_FILE = os.path.join(DOCS_DIR, "review_response.json")

action = sys.argv[1]  # "complete" or "skip"
nonce = sys.argv[2]
task_id = sys.argv[3]

log = open("/data/data/com.termux/files/home/storage/shared/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/action_handler.log", "a")
log.write(f"action={action} nonce={nonce} task_id={task_id}\n")
log.close()

try:
    with open(PENDING_FILE) as f:
        pending = json.load(f)
except:
    pending = []

# 修改这一行，强制转为字符串比较
task = next((t for t in pending if str(t.get("task_id")) == str(task_id)), None)
if not task:
    sys.exit(0)

entry = {
    "task_id": task_id,
    "action": action,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "review_type": task.get("review_type", "simple"),
    "path": task.get("path", ""),
    "tag_content": task.get("tag_content", ""),
    "action_script": task.get("action", "")
}

try:
    with open(RESPONSE_FILE) as f:
        resp = json.load(f)
except:
    resp = []

resp.append(entry)

with open(RESPONSE_FILE, "w") as f:
    json.dump(resp, f, indent=2, ensure_ascii=False)

with open(PENDING_FILE, "w") as f:
    json.dump([t for t in pending if t.get("task_id") != task_id], f, indent=2, ensure_ascii=False)
