# CLAUDE.md

---
name: bilibili-history
description: 获取 Bilibili 观看历史记录并提取摘要。当用户提到"b站历史记录"、"bilibili历史记录"、"获取我的b站观看历史"、"导出b站历史"或"b站视频摘要"时触发。
---

## 脚本位置

`scripts/get_history_byopus.py` — 获取历史记录
`scripts/get_obsidian_abstract_from_json.py` — 从 JSON 提取摘要
`scripts/log_in/get_2dcodec_download_cookie.py` — 后台扫码登录 B 站，获取 Cookie（首次使用或 Cookie 失效时需要先运行此脚本）

## 调用方式

**获取历史记录并保存：**
```bash
python3 scripts/get_history_byopus.py <pn> <ps> -o <输出.json>
```

**从已有 JSON 提取摘要文本：**
```bash
python3 scripts/get_obsidian_abstract_from_json.py <历史记录.json>
```

**查看帮助：**
```bash
python3 scripts/get_history_byopus.py -h
python3 scripts/get_obsidian_abstract_from_json.py -h
```
