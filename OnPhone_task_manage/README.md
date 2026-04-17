# Obsidian 定时计划调度系统

这是一套直接低功耗挂到后台运行的自动化脚本，在 Android 上长期稳定运行，无需人工干预。

## 功能

当你在 Obsidian 笔记中标记计划后，系统会在指定时间自动唤起 Obsidian 并定位到对应位置，帮助你按计划推进。

## 安装

```bash
bash setup_task_manage.sh
```

## 启动

```bash
bash start_task_manage_daemons.sh
```

## 停止

```bash
bash stop_task_manage_daemons.sh
```

## 架构

系统由 3 对监控脚本 + 1 个每日轮询脚本组成：

- **vault 监控**：检测笔记文件变化，自动解析并登记计划任务
- **任务调度**：在计划时间到达前 10 分钟内触发提醒
- **超时处理**：未及时完成的任务在 2 小时内重新安排
- **长期任务**：超过 7 天的计划存入独立队列，每日 23:40 检查是否进入执行窗口

任务数据存储在 `docs/` 目录下的 JSON 文件中，包含当前任务、长期任务和超时待处理三个队列。

## 环境依赖

- Android
- `inotifywait`（文件监控）
- `jq`（JSON 处理）
- Obsidian + Advanced URI 插件

## 测试状态

**已验证可用：**
- `monitor_task_json.sh`
- `monitor_vault_md.sh`
- `review_notification_daemon.sh`
- `review_action_complete.sh`
- `review_action_skip.sh`
- `action_handler.py`
- `scan_task_in_file.py`

**未测试：**
- `review_job_launch.py`
- `ob_task_rearrange.py`
- `monitor_task_abort_json.sh`
- `polling_manage_longterm_task.sh`

## 目录结构

```
OnPhone_task_manage/
├── scripts/           # 核心脚本
├── docs/              # 任务数据与日志
├── tests/             # 自动化测试
├── setup_task_manage.sh
├── start_task_manage_daemons.sh
└── stop_task_manage_daemons.sh
```