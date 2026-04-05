# Obsidian Android CLI

在 Android/Termux 环境下通过命令行操作 Obsidian 库。解决obsidian cli 在android 手机上无法调用问题，方便vibe coding 工具使用obsidian cli时底层调用obsidian命令行工具。

## 安装

### 1. 克隆或复制脚本

```bash
手动将 obsidian.sh 放入 ~/obsidian-cli/
```

### 2. 添加软链接到全局路径

```bash
ln -s ~/obsidian-cli/scripts/obsidian.sh ~/../usr/bin/obsidian
chmod +x ~/obsidian-cli/scripts/obsidian.sh
```

> **原理**：`~/../usr/bin` 是 Termux 的全局命令目录，软链接后可在任意目录直接调用 `obsidian` 命令。

### 3. 修改配置

编辑脚本顶部的配置区：

```bash
VAULT="YourVaultName"                                    # 你的库名
VAULT_PATH="$HOME/storage/shared/Documents/Obsidian"     # 你的库路径
```

### 4. 安装依赖（如尚未安装）

```bash
pkg install ripgrep git coreutils jq
```

### 5. 安装 Obsidian 插件

在 Obsidian 中安装 **Advanced URI** 插件（必需，用于动作类命令）。

## 快速使用

```bash
# 动作类（通过 Advanced URI）
obsidian open path="Daily/2026-04-05.md"
obsidian append path="Log.md" content="2026-04-05: done"
obsidian daily
obsidian search query="project"

# 查询类（本地文件）
obsidian read path="Note.md"
obsidian tags counts sort=count
obsidian tag name="todo" verbose
obsidian links path="Note.md" total
obsidian outline path="Note.md"
obsidian file path="Note.md"
obsidian files folder="Attachments" ext=".pdf"
obsidian folder path="Archive" info="size"
obsidian move path="A.md" to="Archive/A.md"
```

## 依赖

| 工具 | 用途 | 安装 |
|------|------|------|
| ripgrep (rg) | 搜索标签、链接、正则匹配 | `pkg install ripgrep` |
| git | 版本控制、移动文件保持历史 | `pkg install git` |
| coreutils | stat、wc 等基础命令 | `pkg install coreutils` |
| Advanced URI | Obsidian 插件（动作类必需） | Obsidian 社区插件市场 |
