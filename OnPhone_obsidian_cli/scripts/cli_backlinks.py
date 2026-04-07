#!/usr/bin/env python3
# cli_backlinks.py - 提取 frontmatter 中的 backlinks

import sys
import yaml
import re
from pathlib import Path

def extract_frontmatter(content: str) -> tuple[dict, str]:
    """
    提取 frontmatter 和正文
    返回: (frontmatter_dict, body_content)
    """
    if not content.startswith('---'):
        return {}, content
    
    # 找到结束标记
    match = re.search(r'\n---\s*\n', content[3:])
    if not match:
        return {}, content
    
    yaml_content = content[4:3 + match.start()]
    body = content[3 + match.end():]
    
    try:
        fm = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError:
        fm = {}
    
    return fm, body

def get_backlinks(file_path: str) -> list[str]:
    """获取文件的 backlinks 列表"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"错误: 文件不存在 {file_path}", file=sys.stderr)
        sys.exit(1)
    
    content = path.read_text(encoding='utf-8')
    frontmatter, _ = extract_frontmatter(content)
    
    # 支持多种 backlinks 格式
    backlinks = frontmatter.get('backlinks', [])
    
    # 处理不同 YAML 格式: 列表或逗号分隔字符串
    if isinstance(backlinks, str):
        # "file1.md, file2.md" -> ["file1.md", "file2.md"]
        backlinks = [b.strip() for b in backlinks.split(',') if b.strip()]
    elif not isinstance(backlinks, list):
        backlinks = []
    
    return backlinks

def main():
    if len(sys.argv) < 2:
        print("用法: python3 get_backlinks.py <md文件路径>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    backlinks = get_backlinks(file_path)
    
    # 输出格式: 每行一个路径（便于 shell 处理）
    for link in backlinks:
        print(link)

if __name__ == '__main__':
    main()