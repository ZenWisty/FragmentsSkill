---
name: OnPhone_obsidian_cli
description: |
  Obsidian CLI for Android/Termux. 当用户在 Android/鸿蒙手机上通过 Termux 操作 Obsidian 库时触发，包括：vault name、obsidian command、advanced uri (obsidian://advanced-uri)、或任何涉及移动端 Obsidian 文件管理的请求。支持的命令分为两类 — 动作类 (open/append/prepend/daily/command/search/bookmark) 通过 Advanced URI 插件执行，以及查询类 (read/tags/tag/links/backlinks/file/files/folder/folders/outline/move) 通过本地 ripgrep/find/git 操作库文件。当用户提到"Android Obsidian"、"Termux Obsidian"、"obsidian CLI"、"Advanced URI"时也触发。
---

# Obsidian Android CLI

本 skill 让 Claude 能够在 Android/鸿蒙设备的 Termux 环境下，通过 **Advanced URI 插件**（动作类）+ **Termux 原生命令**（查询类）操作 Obsidian 库。

> **为什么不用 Local REST API？** Android 版 Obsidian 运行在 Capacitor 沙盒中，无法绑定端口建立 HTTP 服务器。Advanced URI 是 Android 端唯一的"控制中心"。

## 核心架构

```
Termux + Obsidian (Android)
    ├── 动作类命令 ──→ Advanced URI 插件 (obsidian://advanced-uri)
    └── 查询类命令 ──→ 本地文件操作 (rg/cat/find/git)
```

## 配置

用户需在脚本中修改以下变量：

```bash
VAULT="YourVaultName"                        # Obsidian 库名
VAULT_PATH="$HOME/storage/shared/Documents/Obsidian"  # 库路径
```

## 依赖

- `ripgrep` (rg) — 搜索
- `git` — 版本控制（可选）
- `coreutils` — stat, wc 等
- **Advanced URI 插件** — 必须在 Obsidian 中安装

## 命令速查

### 动作类（通过 Advanced URI / `am start`）

| 命令 | 用途 | 示例 |
|------|------|------|
| `open` | 在 Obsidian 中打开文件 | `obsidian open path="Note.md"` |
| `append` | 向文件追加内容 | `obsidian append path="Note.md" content="text"` |
| `prepend` | 向文件头部插入内容 | `obsidian prepend path="Note.md" content="text"` |
| `daily` | 打开今日日记 | `obsidian daily` |
| `command` | 执行 Obsidian 内部命令 | `obsidian command id="plugin-cmd-id"` |
| `search` | 在 Obsidian 中搜索 | `obsidian search query="keyword"` |
| `bookmark` | 打开书签 | `obsidian bookmark name="name"` |

### 查询类（通过本地文件 / rg cat find git）

| 命令 | 用途 | 示例 |
|------|------|------|
| `read` | 读取文件内容 | `obsidian read path="Note.md"` |
| `tags` | 列出标签 | `obsidian tags [path="f.md"] [total] [counts] [sort=count]` |
| `tag` | 搜索含特定标签的文件 | `obsidian tag name="todo" [total] [verbose]` |
| `links` | 提取 [[link]] 链接 | `obsidian links path="Note.md" [total]` |
| `backlinks` | 查找反链 | `obsidian backlinks path="Note.md"` |
| `file` | 获取文件元信息 | `obsidian file path="Note.md"` |
| `files` | 列出文件 | `obsidian files [folder="Dir"] [ext=".pdf"] [total]` |
| `folder` | 文件夹信息 | `obsidian folder path="Dir" [info=files|folders|size]` |
| `folders` | 列出子文件夹 | `obsidian folders [folder="Dir"] [total]` |
| `outline` | 提取标题大纲 | `obsidian outline path="Note.md" [total]` |
| `move` | 移动文件 | `obsidian move path="A.md" to="Folder/A.md"` |

## 参数解析约定

所有命令接受 `name=value` 或 `name="value"` 格式的参数：

```bash
get_val() {
    echo "$*" | grep -oP "$1=\"?\K[^\" ]+"
}

# 示例
FILE=$(get_val "path" <<< "$args")
TAG=$(get_val "name" <<< "$args")
```

## 高级选项

- `total` — 只输出数量（用于计数类命令）
- `verbose` — 显示详细信息（如文件列表）
- `counts` — 显示每个标签/链接的出现次数
- `sort=count` — 按数量排序（配合 `counts` 使用）
- `ext=".pdf"` — 按扩展名筛选文件
- `info=files|folders|size` — 指定文件夹信息的类型

## 使用示例

### 1. 标签相关

- **搜索特定标签并列出文件**：
    ```
    obsidian tag name="todo" verbose
    ```
- **列出库中所有标签并按数量排序**：
    ```
    obsidian tags counts sort=count
    ```
- **只看某个文件的标签**：
    ```
    obsidian tags path="Daily/2023-10-27.md"
    ```

### 2. 文件与目录

- **查看文件信息**：
    ```
    obsidian file path="Work.md"
    ```
- **列出某个文件夹下的所有 PDF**：
    ```
    obsidian files folder="Attachments" ext=".pdf"
    ```
- **查看文件夹占用空间**：
    ```
    obsidian folder path="Archive" info="size"
    ```

### 3. 链接与结构

- **列出文件的出链数量**：
    ```
    obsidian links path="ProjectA.md" total
    ```
- **显示文章大纲 (Tree 格式)**：
    ```
    obsidian outline path="Meeting_Notes.md"
    ```

### 4. 移动文件

```
obsidian move path="Note.md" to="Archive/Note.md"
```

### 5. 动作类命令

- **在 Obsidian 中打开文件**：
    ```
    obsidian open path="Daily/2023-10-27.md"
    ```
- **追加内容到文件**：
    ```
    obsidian append path="Log.md" content="2026-04-05: did something"
    ```
- **搜索关键词**：
    ```
    obsidian search query="project update"
    ```
- **打开今日日记**：
    ```
    obsidian daily
    ```

## 注意事项

1. **URL 编码**：`am start` 发送的 `data` 参数中特殊字符需手动 URL 编码（如空格→%20）
2. **路径**：所有路径相对于 `VAULT_PATH`，不要包含 vault 路径前缀
3. **git mv**：移动文件时优先使用 git mv 保持版本历史
4. **Android Intent**：`am start` 用于发送 Intent 打开 Obsidian，使用 `> /dev/null 2>&1` 抑制输出
