#!/usr/bin/env python3
# cli_backlinks.py - 读取/计算并写入 frontmatter backlinks 字段

import sys
import os
import re
import yaml
import glob as glob_module
from pathlib import Path

def extract_frontmatter(content: str) -> tuple[dict, str, int]:
    """
    提取 frontmatter 和正文
    返回: (frontmatter_dict, body_content, frontmatter_end_pos)
    frontmatter_end_pos = 内容开始处（含\n---\n）的位置，用于后续重写
    """
    if not content.startswith('---'):
        return {}, content, 0

    # 找到结束标记（\n---\n 或 \n---）
    match = re.search(r'\n---\s*\n', content[3:])
    if not match:
        # 有 --- 但没有结束，找不到有效的 frontmatter
        return {}, content, 0

    end_pos = 3 + match.end()  # 内容开始的位置（\n后的第一个字符）
    yaml_content = content[4:3 + match.start()]

    try:
        fm = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError:
        fm = {}

    return fm, content, end_pos


def get_backlinks(file_path: str) -> list[str]:
    """获取文件的 backlinks 列表（仅读取，不计算）"""
    path = Path(file_path)

    if not path.exists():
        print(f"错误: 文件不存在 {file_path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding='utf-8')
    frontmatter, _, _ = extract_frontmatter(content)

    backlinks = frontmatter.get('backlinks', [])

    if isinstance(backlinks, str):
        backlinks = [b.strip() for b in backlinks.split(',') if b.strip()]
    elif not isinstance(backlinks, list):
        backlinks = []

    return backlinks


def has_backlinks_field(file_path: str) -> bool:
    """检查 frontmatter 中是否显式定义了 backlinks 字段"""
    path = Path(file_path)
    if not path.exists():
        return False
    content = path.read_text(encoding='utf-8')
    frontmatter, _, _ = extract_frontmatter(content)
    return 'backlinks' in frontmatter


def compute_backlinks(file_path: str, vault_path: str) -> list[str]:
    """
    计算文件的 backlinks：
    扫描 vault 中所有 .md 文件，查找 wikilink [[basename]] 指向本文件的所有文档
    file_path: 目标文件的相对路径（相对于 vault）
    vault_path: vault 绝对路径
    """
    target = Path(file_path)
    target_name = target.name                          # "笔记.md"
    target_stem = target.stem                           # "笔记"
    target_full = target.as_posix()                     # "目录/笔记.md"
    target_full_stem = target.with_suffix('').as_posix() # "目录/笔记"

    backlinks = []

    pattern = str(Path(vault_path) / '**' / '*.md')
    for md_path in glob_module.iglob(pattern, recursive=True):
        # 跳过 .obsidian、.git 等目录
        if '/.git/' in md_path or '/.obsidian/' in md_path or '/.claude/' in md_path or '/.trash/' in md_path:
            continue
        if md_path == str(target):
            continue

        try:
            text = Path(md_path).read_text(encoding='utf-8')
        except Exception:
            continue

        # 提取所有 [[...]] wikilink 目标
        # 匹配 [[target]] 或 [[target|alias]] 或 [[target#heading]]
        for m in re.finditer(r'\[\[([^\]#|]+)(?:[|#][^\]]*)?\]\]', text):
            link_target = m.group(1).strip()
            # 支持：[[笔记]] 或 [[目录/笔记]]（target_stem=笔记, target_full_stem=目录/笔记）
            if link_target == target_stem or link_target == target_full_stem or link_target == target_name:
                rel = Path(md_path).relative_to(vault_path).as_posix()
                if rel not in backlinks:
                    backlinks.append(rel)
                break  # 找到一个匹配就够了

    backlinks.sort()
    return backlinks


def write_backlinks(file_path: str, backlinks: list[str]):
    """将 backlinks 列表写入文件的 frontmatter（保留其他字段）"""
    path = Path(file_path)
    content = path.read_text(encoding='utf-8')
    frontmatter, body, end_pos = extract_frontmatter(content)

    if end_pos == 0:
        # 无 frontmatter，在文件开头插入
        new_fm = yaml.safe_dump({'backlinks': backlinks}, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_fm}---\n{content}"
    else:
        # 保留原有 frontmatter，更新 backlinks 字段
        frontmatter['backlinks'] = backlinks
        new_fm = yaml.safe_dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_fm}---\n{body}"

    path.write_text(new_content, encoding='utf-8')


def main():
    if len(sys.argv) < 2:
        print("用法: python3 cli_backlinks.py <md文件相对路径> [vault绝对路径]", file=sys.stderr)
        sys.exit(1)

    rel_path = sys.argv[1]
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH') or (sys.argv[2] if len(sys.argv) > 2 else None)

    if not vault_path:
        print("错误: 未设置 OBSIDIAN_VAULT_PATH 环境变量或缺少 vault_path 参数", file=sys.stderr)
        sys.exit(1)

    # 拼接目标文件的绝对路径
    target_abs = str(Path(vault_path).absolute() / rel_path)

    # 检查 frontmatter 是否有 backlinks 字段
    if has_backlinks_field(target_abs):
        backlinks = get_backlinks(target_abs)
    else:
        # 计算 backlinks 并写入 frontmatter
        backlinks = compute_backlinks(rel_path, vault_path)
        write_backlinks(target_abs, backlinks)

    for link in backlinks:
        print(link)


if __name__ == '__main__':
    main()
