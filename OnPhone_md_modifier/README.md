# OnPhone Md Modifier

Android Termux 环境下通过脚本管理 Obsidian Vault 中 markdown 文件的工具集。

## Directory Structure

```
OnPhone_md_modifier/
├── CLAUDE.md              # Claude Code 工作指引
├── README.md              # 本文件
├── scripts/
│   ├── obsidian_modifier_nohop.sh   # 编辑模式：打开文件 + 后台监控 + 自动提交
│   └── obsidian_viewfile.sh         # 查看模式：快速打开文件（可选行号跳转）
└── skills/
    └── on-phone-md-modifier-obsidian/
        └── SKILL.md       # Claude Code Skill：用于判定调用哪个脚本
```

## Skills

### on-phone-md-modifier-obsidian

Claude Code Skill，根据用户意图选择脚本：

| 用户意图 | 调用的脚本 | 行为 |
|---------|-----------|------|
| **修改/编辑** 文件 | `obsidian_modifier_nohop.sh` | 打开 Obsidian → 20分钟静默 → 监控文件变动 → 自动 git commit/push |
| **查看/浏览** 文件 | `obsidian_viewfile.sh` | 直接打开文件，支持行号跳转，无后台监控 |

**触发场景**：
- "open file X in Obsidian"
- "edit my notes" / "modify the daily note"
- "view the meeting notes"
- 任何在 Obsidian Vault 中打开/编辑/查看 .md 文件的请求

**安装**：将该 skill 目录复制到 Claude Code 的 skills 加载目录即可使用。
