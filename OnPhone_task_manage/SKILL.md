---
name: obsidian-task-manage
description: Obsidian 间隔复习任务调度系统的开发与维护。当用户提到 Obsidian 复习任务、task.json 调度、间隔重复(spaced repetition)、[##[review: dates] ##] 标签、复习提醒、任务队列管理、或涉及 OnPhone_task_manage 项目时触发。主动询问用户是否需要启动或停止后台服务。
---

# Obsidian 任务调度系统 (obsidian-task-manage)

## 项目概述

运行在 Android/Termux 上的 Obsidian 间隔复习调度系统，通过监控 `.md` 文件中的 `[##[review: dates] ##]` 标签，自动安排和触发复习任务。

## 架构：3 对 Daemon + 1 个轮询

| Daemon 对 | 职责 |
|-----------|------|
| `monitor_vault_md.sh` → `scan_task_in_file.py` | vault 文件变化 → 解析 review 标签 → 写入 task.json |
| `monitor_task_json.sh` → `review_job_launch.py` | 任务到期（10分钟内）→ 追加时间戳到 .md → 唤起 Obsidian |
| `monitor_task_abort_json.sh` → `ob_task_rearrange.py` | 过期任务进入 abort → 2小时内重新安排 |
| `polling_manage_longterm_task.sh` | 每日 23:40 将 longterm 进入7天窗口的任务迁入 task.json |

## 核心文件

```
OnPhone_task_manage/
├── scripts/
│   ├── scan_task_in_file.py       # review 标签解析 + func1 算法 + longterm 分流
│   ├── ob_task_rearrange.py       # abort 任务捞回 + 碰撞检测 find_next_available_slot
│   ├── review_job_launch.py        # 追加时间戳到 .md + 唤起 Obsidian（Advanced URI）
│   ├── monitor_vault_md.sh          # inotifywait 监控 vault 目录
│   ├── monitor_task_json.sh        # 监听 task.json，到期触发 review
│   ├── monitor_task_abort_json.sh  # 监听 task_abort.json，过期触发 rearrange
│   └── polling_manage_longterm_task.sh  # 每日 longterm → task.json 迁转
├── docs/
│   ├── task.json                  # 7天内任务队列（按时间排序）
│   ├── task_longterm.json         # 超过7天的任务队列
│   ├── task_abort.json             # 过期待捞回的任务
│   └── logs/                       # 各 daemon 运行日志
├── start_task_manage_daemons.sh   # 启动所有 daemon（检查依赖）
├── stop_task_manage_daemons.sh    # 停止所有 daemon（按 PID 文件终止）
└── setup_task_manage.sh           # 安装脚本：将启动/停止快捷方式安装到 ~/.shortcuts/
```

## func1() 复习间隔算法

根据 review 历史次数计算下次复习时间：

| 复习次数 | 间隔 |
|---------|------|
| 0（空标签） | 现在 + 20 分钟 |
| 1 | 上次复习 + 12 小时 |
| 2 | 上次复习 + 6 天 |
| 3 | 上次复习 + 10 天 |
| 4 | 上次复习 + 3 个月 |
| 5+ | 不再安排 |

**休息时间顺延**：若落在 23:30 → 次日 07:45，自动移到次日 07:45。

**7 天分流**：计算结果 > 7 天的任务写入 `task_longterm.json`，由 polling 脚本在到期前 7 天迁入 `task.json`。

## review 标签格式

```
[##[review: 2026-04-01 10:00:00, 2026-04-05 10:00:00] ##]
```

逗号分隔的时间列表，复习后自动追加新的时间戳。

## 启动与停止

**首次安装**：
```bash
bash /path/to/setup_task_manage.sh
```

**启动所有 daemon**：
```bash
bash start_task_manage_daemons.sh
# 或在 Termux 中通过快捷方式：start_task_manage_daemons
```

**停止所有 daemon**：
```bash
bash stop_task_manage_daemons.sh
# 或：stop_task_manage_daemons
```

**单次扫描某个文件**（手动触发）：
```bash
python3 scripts/scan_task_in_file.py /path/to/note.md
```

## PID 文件单例

每个 daemon 启动时会创建 `docs/<name>.pid` 文件记录自身 PID，重复启动时检测该 PID 是否存活，避免多实例运行。Android 不支持 `flock`，使用 `kill -0 $PID` 检测。

## 环境要求

- Android/Termux
- `inotifywait`（inotify-tools）
- `jq`（JSON 处理）
- Obsidian + Advanced URI 插件（用于精确跳转到标签所在行）

## 测试

`tests/` 目录下包含模块验证和本地环境内的实地测试，覆盖核心算法、脚本逻辑和端到端流程。
