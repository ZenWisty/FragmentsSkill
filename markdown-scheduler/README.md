# markdown-scheduler
这个 Skill 用于安排环境，用于定时执行基于 Markdown 文件的任务。
包含 .py 脚本，需要运行环境

### prerequisites
 apscheduler filelock watchdog anthropic     is needed.

### 使用方法


### details
1. 全局需要修改、使用的配置文件默认位置：~/.config/ai_scheduler/task.json 和 ~/.config/ai_scheduler/archive.json，可在 @/scripts/scheduler.py 中修改
2. 所有修改 task.json 和 archive.son 的操作都使用了 FileLock 的操作保证写入的原子性，由于目前我的文档系统操作不复杂，因此暂时不纳入SQLite等数据库的操作。 但是仍然方便修改成数据库操作，仅需修改 @/scripts/scheduler.py 中的 safe_load_tasks 和 safe_save_tasks 函数即可
3. 由于当前自建服务器上的文档解码方式是自用、个人定制的，因此此处没有开放markdown文件的解码功能，即@/scripts/scheduler.py 中的 scan_and_sync 函数。如需使用，可以自制设置 schedule 基于文档的计划任务的功能，简单替换 scan_and_sync 函数中的逻辑即可(parser_c.so 是手机操作系统本地编译出来的，依赖各自环境，因此也必须替换)