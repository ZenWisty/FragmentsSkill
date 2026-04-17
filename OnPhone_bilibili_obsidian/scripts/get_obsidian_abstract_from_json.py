#!/data/data/com.termux/files/usr/bin/python3
"""
从 Bilibili 历史记录 JSON 中提取视频标题、URL 和副标题（CC字幕），
输出为整段纯文本，供存入 Obsidian 等笔记使用。
"""

import json
import os
import sys


def get_video_url(video):
    """从视频信息提取 B 站 URL"""
    bvid = video.get("bvid")
    aid = video.get("aid")
    if bvid:
        return f"https://www.bilibili.com/video/{bvid}"
    elif aid:
        return f"https://www.bilibili.com/video/av{aid}"
    return video.get("redirect_link", "未知地址")


def print_help():
    """打印帮助信息"""
    help_text = """\
用法: python3 get_obsidian_abstract_from_json.py <json文件路径>

从 get_history_byopus.py 保存的 JSON 文件中读取视频信息，
输出每条视频的标题、URL 和副标题（CC字幕）。

输出格式:
  视频标题: <标题>
  视频地址: <url>
  字幕文本: <字幕内容>

如果该视频没有字幕，字幕文本显示为"（无字幕）"。

示例:
  python3 get_obsidian_abstract_from_json.py ~/bilibili_history.json
"""
    print(help_text)


def extract_abstracts(json_path):
    """
    读取 JSON 文件，提取所有视频的标题、URL、字幕

    Args:
        json_path: JSON 文件路径

    Returns:
        str: 整合后的文本段落
    """
    if not os.path.exists(json_path):
        print(f"❌ 文件不存在: {json_path}")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        sys.exit(1)

    videos = data.get("data", {}).get("videos", [])
    if not videos:
        print("❌ JSON 中未找到视频数据")
        sys.exit(1)

    lines = []
    for video in videos:
        title = video.get("title", "未知标题")
        url = get_video_url(video)
        subtitle = video.get("subtitle_text", "").strip()

        lines.append(f"视频标题: {title}")
        lines.append(f"视频地址: {url}")
        lines.append(f"字幕文本: {subtitle if subtitle else '（无字幕）'}")
        lines.append("")  # 空行分隔

    return "\n".join(lines).strip()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    json_path = sys.argv[1]
    result = extract_abstracts(json_path)
    print(result)


if __name__ == "__main__":
    main()
