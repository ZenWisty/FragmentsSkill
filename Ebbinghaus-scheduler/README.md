# ebbinghaus-scheduler

Task timing scheduling module for arranging tasks with spaced repetition timing.

## Installation

```bash
pip install re json datetime
```

## Usage

### 1. Python API 调用

```python
# 方式一：直接导入（推荐，需确保项目路径在 sys.path）
from scripts.Ebbinghaus import curve_api, adjust_current_task

# 方式二：手动添加路径
import sys
sys.path.insert(0, '/path/to/Ebbinghaus-scheduler')
from scripts.Ebbinghaus import curve_api, adjust_current_task

# 计算下一个时间点
next_time, updated_tag = curve_api("[## Task [review:] ##]")

# 安排 2 小时内的任务
results = adjust_current_task(['[## Task1 [review:] ##]', '[## Task2 [review:] ##]'])
```

### 2. Claude Skill 调用

在其他 Claude 对话中使用此 Skill：

1. **触发方式**：在对话中提及以下关键词：
   - "schedule task"
   - "add review time"
   - "arrange tasks"
   - "Ebbinghaus"
   - 操作 `[review:]` 标签

2. **手动激活**：将 `SKILL.md` 内容复制到对话中或使用 Skill 管理器加载

3. **调用示例**：
   ```
   user: 请使用 Ebbinghaus scheduler 为这个标签安排时间：[## 任务 [review:] ##]
   ```

## Testing

```bash
cd scripts
python -m pytest test_ebbinghaus.py -v
```

Run specific test class:
```bash
python -m pytest test_ebbinghaus.py::TestCurveApi -v
```

Run single test:
```bash
python -m pytest test_ebbinghaus.py::TestCurveApi::test_empty_tag -v
```

## File Structure

```
Ebbinghaus-scheduler/
├── SKILL.md
├── README.md
├── scripts/
│   ├── __init__.py
│   ├── Ebbinghaus.py       # Core module
│   └── test_ebbinghaus.py  # Unit tests
└── .claude/
    └── settings.json
```