#!/usr/bin/env python3
# get_backlinks_full.py - 完整版，支持统计和验证

import sys
import yaml
import re
import os
from pathlib import Path
from datetime import datetime

class BacklinkAnalyzer:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
    
    def extract_frontmatter(self, content: str) -> dict:
        """提取 frontmatter"""
        if not content.startswith('---'):
            return {}
        
        match = re.search(r'\n---\s*\n', content[3:])
        if not match:
            return {}
        
        yaml_content = content[4:3 + match.start()]
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            return {}
    
    def get_backlinks(self, file_path: str) -> dict:
        """
        获取 backlinks 并验证文件是否存在
        返回: {
            'backlinks': [...],      # 原始列表
            'existing': [...],       # 存在的文件
            'missing': [...],        # 不存在的文件（死链）
            'count': N               # 总数
        }
        """
        path = self.vault_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        if not path.exists():
            return {'error': f'文件不存在: {path}'}
        
        content = path.read_text(encoding='utf-8')
        fm = self.extract_frontmatter(content)
        
        backlinks = fm.get('backlinks', [])
        if isinstance(backlinks, str):
            backlinks = [b.strip() for b in backlinks.split(',') if b.strip()]
        elif not isinstance(backlinks, list):
            backlinks = []
        
        # 验证每个 backlink 是否存在
        existing = []
        missing = []
        
        for link in backlinks:
            # 处理相对路径
            if not link.startswith('/'):
                link_path = self.vault_path / link
            else:
                link_path = Path(link)
            
            if link_path.exists():
                existing.append(str(link))
            else:
                missing.append(str(link))
        
        return {
            'file': str(path),
            'title': fm.get('title', path.stem),
            'backlinks': backlinks,
            'existing': existing,
            'missing': missing,
            'count': len(backlinks),
            'valid_count': len(existing),
            'has_frontmatter': bool(fm)
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='获取 Obsidian 文件的 backlinks')
    parser.add_argument('file', help='Markdown 文件路径')
    parser.add_argument('--vault', '-v', default=os.getenv('OBSIDIAN_VAULT', '.'),
                       help='Vault 根目录')
    parser.add_argument('--json', '-j', action='store_true',
                       help='输出 JSON 格式')
    parser.add_argument('--check', '-c', action='store_true',
                       help='验证 backlink 文件是否存在')
    
    args = parser.parse_args()
    
    analyzer = BacklinkAnalyzer(args.vault)
    result = analyzer.get_backlinks(args.file)
    
    if 'error' in result:
        print(f"错误: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.check:
        # 详细验证模式
        print(f"📄 文件: {result['file']}")
        print(f"📝 标题: {result['title']}")
        print(f"🔗 Backlinks 总数: {result['count']}")
        print(f"✅ 有效链接: {result['valid_count']}")
        print(f"❌ 死链: {len(result['missing'])}")
        
        if result['existing']:
            print("\n有效链接:")
            for link in result['existing']:
                print(f"  ✓ {link}")
        
        if result['missing']:
            print("\n死链:")
            for link in result['missing']:
                print(f"  ✗ {link}")
    else:
        # 简洁模式: 只输出 backlink 路径（兼容 shell 处理）
        for link in result['backlinks']:
            print(link)

if __name__ == '__main__':
    main()