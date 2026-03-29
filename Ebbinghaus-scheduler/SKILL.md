---
name: ebbinghaus-scheduler
description: Schedule and arrange tasks using the Ebbinghaus spaced repetition timing algorithm. Use when the user wants to calculate the next scheduled time for a task tag, adjust task density within 2-hour windows, or arrange tasks with AI assistance. Triggers when user mentions 'schedule task', 'add review time', 'arrange tasks', 'Ebbinghaus', or manipulating `[review:]` tags in markdown.
---

## Calling Methods

### 1. Python API

```python
# 方式一：直接导入（推荐，需确保项目路径在 sys.path）
from scripts.Ebbinghaus import curve_api, adjust_current_task

# 方式二：手动添加路径
import sys
sys.path.insert(0, '/path/to/Ebbinghaus-scheduler')
from scripts.Ebbinghaus import curve_api, adjust_current_task
```

### 2. Claude Skill

**触发方式**：提及 "schedule task", "add review time", "arrange tasks", "Ebbinghaus", 或操作 `[review:]` 标签

**手动激活**：将 SKILL.md 内容复制到对话中或使用 Skill 管理器加载

## Core Functions

### 1. curve_api(tag_content) - Calculate Next Time

**Input:** A tag string containing `[review:]` (may be empty or have multiple timestamps)

**Output:** `(next_time: datetime, updated_tag: str)`

**Logic:**
- Parse existing timestamps from `[review:]`
- If already has 5 timestamps, return `(None, tag_content)` (no changes)
- Calculate next time based on existing count:
  - 0 times → now + 25 minutes
  - 1 time → now + 12 hours
  - 2 times → now + 7 days
  - 3 times → now + 15 days
  - 4 times → now + 90 days (3 months)
- Append new timestamp to `[review:]` and return updated tag

**Example:**
```python
# Input: "[## Task [review:] ##]"
# Output: (datetime_obj, "[## Task [review:2026-03-29T15:30:00] ##]")
```

### 2. adjust_current_task(tag_contents_list) - Arrange Tasks

**Input:** List of tag strings from tasks scheduled within 2 hours

**Output:** List of `{"time": "ISO_string", "content": "updated_tag"}`

**Logic:**
1. Retrieve tag context via `md_modifier.read_md_tag_content(tag)` (TODO)
2. Display task summary for user
3. Ask user whether to use AI assistance:
   - **Yes:** Call `rearrange_task_assist` (MiniMax Claude API) for smart arrangement
   - **No:** Default to equal-spacing within the 2-hour window
4. Update each tag's `[review:]` first unexpired timestamp
5. Return list of `{time, content}` pairs

## AI Arrangement (MiniMax Backend)

When AI assistance is requested, use the following API configuration (TODO: confirm):
```python
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-Text-01"

client = Anthropic(api_key=api_key, base_url=MINIMAX_BASE_URL)
```

## Dependencies

| Module | Status | Description |
|--------|--------|-------------|
| `md_modifier` | TODO | Document editor, provides `read_md_tag_content(tag)` |
| `Anthropic` SDK | TODO | MiniMax API, provides `rearrange_task_assist` |

## File Structure

```
Ebbinghaus-scheduler/
├── SKILL.md           # This file
├── README.md          # Setup and prerequisites
├── CLAUDE.md          # Claude Code guidance
├── scripts/
│   ├── __init__.py
│   ├── Ebbinghaus.py       # Core scheduling module
│   └── test_ebbinghaus.py  # Unit tests
└── .claude/
    └── settings.json
```