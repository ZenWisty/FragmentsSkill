# -*- coding: utf-8 -*-
"""
Communication module for pending/response JSON files
used between monitor_task_json.sh and ReviewHelperApp.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict

PENDING_FILE = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/review_pending.json"
RESPONSE_FILE = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/review_response.json"


def read_pending() -> List[Dict]:
    """Read all pending tasks from review_pending.json"""
    if not os.path.exists(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def write_pending(tasks: List[Dict]) -> None:
    """Write all pending tasks to review_pending.json"""
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def add_pending_task(task_time: str, path: str, tag_content: str,
                     action: str, review_type: str = "simple") -> str:
    """
    Add a new task to review_pending.json.
    Returns the generated task_id.
    """
    task_id = str(uuid.uuid4())
    task = {
        "task_id": task_id,
        "task_time": task_time,
        "path": path,
        "tag_content": tag_content,
        "action": action,
        "review_type": review_type,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tasks = read_pending()
    tasks.append(task)
    write_pending(tasks)
    return task_id


def remove_pending_task(task_id: str) -> None:
    """Remove a task from review_pending.json by task_id"""
    tasks = [t for t in read_pending() if t.get("task_id") != task_id]
    write_pending(tasks)


def read_pending_by_id(task_id: str) -> Optional[Dict]:
    """Read a specific task from review_pending.json by task_id"""
    tasks = read_pending()
    for t in tasks:
        if t.get("task_id") == task_id:
            return t
    return None


def read_responses() -> List[Dict]:
    """Read all responses from review_response.json"""
    if not os.path.exists(RESPONSE_FILE):
        return []
    try:
        with open(RESPONSE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def write_response(task_id: str, action: str,
                   review_type: str = "simple",
                   path: str = "",
                   tag_content: str = "",
                   action_script: str = "") -> None:
    """
    Write a response for a task (complete or skip).
    Appends to review_response.json.
    Includes path/tag_content for monitor to match against task.json.
    """
    response = {
        "task_id": task_id,
        "action": action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_type": review_type,
        "path": path,
        "tag_content": tag_content,
        "action_script": action_script
    }
    responses = read_responses()
    responses.append(response)
    with open(RESPONSE_FILE, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=2, ensure_ascii=False)


def read_and_clear_response(task_id: str) -> Optional[Dict]:
    """
    Read response for a specific task_id and clear it from the file.
    Returns the response dict or None if not found.
    """
    responses = read_responses()
    target = None
    remaining = []
    for r in responses:
        if r.get("task_id") == task_id:
            target = r
        else:
            remaining.append(r)
    if remaining:
        with open(RESPONSE_FILE, 'w', encoding='utf-8') as f:
            json.dump(remaining, f, indent=2, ensure_ascii=False)
    else:
        if os.path.exists(RESPONSE_FILE):
            os.remove(RESPONSE_FILE)
    return target


def clear_all_pending() -> None:
    """Clear all pending tasks"""
    write_pending([])


def clear_all_responses() -> None:
    """Clear all responses"""
    if os.path.exists(RESPONSE_FILE):
        os.remove(RESPONSE_FILE)
