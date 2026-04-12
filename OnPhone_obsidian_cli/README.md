# Obsidian 手机 CLI

在任何地方用手机或便携设备管理本地 Obsidian 库的轻量 CLI 工具。由于我不喜欢携带大件计算设备出门，但喜欢外出办公，希望随时本地 vibe coding + 自动化管理库。

## 背景

Obsidian CLI 官方不支持移动端。于是在手机上写了一套底层实现，打通移动端 Obsidian 与大模型的调用链路。

## 安装

```bash
# 1. 放入脚本
cp -r obsidian.sh ~/obsidian-cli/

# 2. 软链接到全局命令
ln -s ~/obsidian-cli/scripts/obsidian.sh ~/../usr/bin/obsidian
chmod +x ~/obsidian-cli/scripts/obsidian.sh

# 3. 修改脚本顶部配置
VAULT="你的库名"
VAULT_PATH="$HOME/storage/shared/你的库路径"

# 4. 安装依赖
pkg install ripgrep git coreutils jq

# 5. 在 Obsidian 中安装 Advanced URI 插件（动作类命令必需）
```

## 常用命令

```bash
# 动作类（通过 Advanced URI）
obsidian open path="笔记.md"
obsidian append path="Log.md" content="内容"
obsidian daily

# 查询类（本地文件直读）
obsidian read path="笔记.md"
obsidian tags counts
obsidian links path="笔记.md"
obsidian backlinks path="笔记.md"
obsidian outline path="笔记.md"
obsidian file path="笔记.md"
obsidian files folder="文件夹"
obsidian folders
obsidian search query="关键词"
```

## 依赖

| 工具 | 说明 |
|------|------|
| ripgrep | 搜索 |
| git | 版本控制 |
| coreutils | 基础命令 |
| Advanced URI 插件 | 动作类命令（打开/追加等） |
