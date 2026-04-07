#!/usr/bin/env python3
# check.py - 验证并补全文档的反向链接
# 用法: python3 check.py <目标文档路径> "<backlink文档1路径>|<backlink文档2路径>|..."

import sys
import re
import os
from pathlib import Path

def parse_frontmatter(content: str):
    """
    提取 frontmatter 和正文
    返回: (frontmatter_dict, frontmatter_raw_text, body_content)
    """
    if not content.startswith('---'):
        return {}, "", content
    
    # 找到结束标记
    match = re.search(r'\n---\s*\n', content[3:])
    if not match:
        return {}, "", content
    
    yaml_start = 4
    yaml_end = 3 + match.start()
    body_start = 3 + match.end()
    
    yaml_content = content[yaml_start:yaml_end]
    body = content[body_start:]
    
    # 简单 YAML 解析（只处理 key: value 和 - 列表）
    fm = {}
    current_key = None
    current_list = []
    
    for line in yaml_content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # 列表项
        if stripped.startswith('- '):
            if current_key:
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        
        # 新的 key
        if ':' in stripped:
            # 保存之前的列表
            if current_key and current_list:
                fm[current_key] = current_list
                current_list = []
            
            key, value = stripped.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if value:
                # 标量值
                fm[key] = value.strip('"').strip("'")
                current_key = None
            else:
                # 可能是列表的开始
                current_key = key
    
    # 保存最后的列表
    if current_key and current_list:
        fm[current_key] = current_list
    
    return fm, yaml_content, body

def build_frontmatter(fm: dict) -> str:
    """将 frontmatter 字典重建为 YAML 字符串"""
    lines = []
    
    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                # 如果包含特殊字符，加引号
                if ':' in item or '#' in item or '[' in item:
                    lines.append(f"  - \"{item}\"")
                else:
                    lines.append(f"  - {item}")
        else:
            # 标量值
            if ':' in str(value) or str(value).startswith('['):
                lines.append(f"{key}: \"{value}\"")
            else:
                lines.append(f"{key}: {value}")
    
    return '\n'.join(lines)

def check_and_update_backlink(target_path: str, backlink_file: str, vault_root: str = "") -> bool:
    """
    检查单个文件的 backlinks 是否包含 target_path
    如果没有，添加进去并保存文件
    返回: 是否进行了修改
    """
    # 解析路径
    target = Path(target_path)
    backlink = Path(backlink_file)
    
    # 如果提供了 vault_root，转换相对路径
    if vault_root:
        backlink_full = Path(vault_root) / backlink
    else:
        backlink_full = backlink
    
    if not backlink_full.exists():
        print(f"  ⚠️  跳过: 文件不存在 {backlink_full}", file=sys.stderr)
        return False
    
    # 读取文件
    try:
        content = backlink_full.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ❌ 错误: 无法读取 {backlink_full}: {e}", file=sys.stderr)
        return False
    
    # 解析 frontmatter
    fm, yaml_raw, body = parse_frontmatter(content)
    
    # 获取当前 backlinks
    backlinks = fm.get('backlinks', [])
    if isinstance(backlinks, str):
        backlinks = [b.strip() for b in backlinks.split(',') if b.strip()]
    elif not isinstance(backlinks, list):
        backlinks = []
    
    # 标准化目标路径（用于比较）
    # 如果 target 是绝对路径，转换为相对 vault 的路径
    target_str = str(target_path)
    if vault_root and target_str.startswith(vault_root):
        target_str = target_str[len(vault_root):].lstrip('/')
    
    # 检查是否已存在
    # 支持多种路径格式比较
    target_variants = {
        target_str,
        target_str.replace('\\', '/'),
        Path(target_str).name,  # 仅文件名
        str(Path(target_str)).replace('\\', '/'),
    }
    
    existing_variants = set()
    for bl in backlinks:
        existing_variants.add(bl)
        existing_variants.add(bl.replace('\\', '/'))
        existing_variants.add(Path(bl).name)
    
    # 检查是否有交集
    if target_variants & existing_variants:
        print(f"  ✅ {backlink}: 已包含 backlink")
        return False
    
    # 直接使用 target_str（相对于 vault 的路径），不做 relpath 计算
    relative_target = target_str.replace('\\', '/')
    
    # 添加到 backlinks
    backlinks.append(relative_target)
    fm['backlinks'] = backlinks
    
    # 重建文件
    new_yaml = build_frontmatter(fm)
    new_content = f"---\n{new_yaml}\n---\n\n{body}"
    
    # 写回文件
    try:
        backlink_full.write_text(new_content, encoding='utf-8')
        print(f"  ➕ {backlink}: 已添加 backlink -> {relative_target}")
        return True
    except Exception as e:
        print(f"  ❌ 错误: 无法写入 {backlink_full}: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python3 check.py <目标文档路径> \"<backlink文档1>|<backlink文档2>|...\"", file=sys.stderr)
        print("示例: python3 check.py \"笔记A.md\" \"笔记B.md|笔记C.md|folder/笔记D.md\"", file=sys.stderr)
        sys.exit(1)
    
    target_path = sys.argv[1]
    backlink_list_str = sys.argv[2]
    vault_root = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # 解析 backlink 列表（| 分隔）
    if backlink_list_str.strip():
        backlink_files = [f.strip() for f in backlink_list_str.split('|') if f.strip()]
    else:
        backlink_files = []
    
    print(f"📄 目标文档: {target_path}")
    print(f"🔍 检查 {len(backlink_files)} 个文档的 backlinks:")
    
    modified_count = 0
    checked_count = 0
    
    for backlink_file in backlink_files:
        checked_count += 1
        if check_and_update_backlink(target_path, backlink_file, vault_root):
            modified_count += 1
    
    print(f"\n📊 统计: 检查了 {checked_count} 个文件, 修改了 {modified_count} 个文件")
    
    # 返回码: 0 = 成功, 1 = 有修改（便于 shell 脚本判断）
    sys.exit(0 if modified_count == 0 else 1)

if __name__ == '__main__':
    main()