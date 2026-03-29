---
name: markdown-tag-parser
description: Parse and extract review tags from markdown files. Use when the user wants to scan markdown files for `[## ... ##]` review blocks, extract timestamps from `[review:]` tags, or generate a task list with next review times. Triggers when user mentions 'parse markdown', 'extract review tags', 'scan review blocks', or 'get scheduled tasks from markdown'.
---

## Usage

Import and call `parse_to_v2_tasks(file_list, schedule_logic_func)`.

**Input:**
- `file_list`: list of markdown file paths (strings)
- `schedule_logic_func`: callback function that receives a list of timestamp strings (from `[review:]`) and returns the next `datetime` for review (or `None` if no review needed)

**Output:**
List of dictionaries, each containing:
- `"time"`: ISO format datetime string of next review
- `"file"`: file path where the block was found
- `"content"`: the full `[## ... ##]` block text

**Example:**
```python
from scripts.parser_c import parse_to_v2_tasks

# Your scheduling function (e.g., Ebbinghaus curve)
def my_schedule(timestamps):
    # compute and return next datetime, or None
    ...

tasks = parse_to_v2_tasks(["notes.md", "journal.md"], my_schedule)
```
