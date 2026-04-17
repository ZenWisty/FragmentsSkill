#!/data/data/com.termux/files/usr/bin/python3
"""
Bilibili 历史记录获取脚本 (by opus)
功能：
1. 获取 Bilibili 观看历史记录，支持分页
2. 返回 JSON 格式的原始视频信息
3. 生成视频 URL
"""

import requests
import os
import json
import sys
import datetime

COOKIE_FILE = os.path.expanduser("~/.bili_cookie")

# 注意：User-Agent 建议模拟真实的 PC 端浏览器，防拦截概率更低
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def load_cookie():
    """检查并读取 Cookie 文件"""
    if not os.path.exists(COOKIE_FILE):
        print("❌ 未找到 Cookie 文件，请先运行扫码登录脚本！")
        return None

    with open(COOKIE_FILE, "r") as f:
        cookie_str = f.read().strip()

    if not cookie_str:
        print("❌ Cookie 文件为空！")
        return None

    return cookie_str


def fetch_history(pn=1, ps=20):
    """
    获取 Bilibili 观看历史记录

    Args:
        pn: 页码（从1开始）
        ps: 每页数量（建议10-600）

    Returns:
        dict: 包含 code, message, data(keys: videos, total) 的字典，
              失败时返回 None
    """
    cookie_str = load_cookie()
    if not cookie_str:
        return None

    # 将 Cookie 加入请求头
    headers = HEADERS.copy()
    headers["Cookie"] = cookie_str

    print(f"🔄 正在请求 Bilibili 历史记录 API (pn={pn}, ps={ps})...", file=sys.stderr)

    # v2/history API，支持 pn/ps 参数
    api_url = "https://api.bilibili.com/x/v2/history"

    try:
        response = requests.get(api_url, params={"pn": pn, "ps": ps}, headers=headers, timeout=10)
        result = response.json()

        code = result.get("code")
        if code == 0:
            data = result.get("data", [])
            print(f"✅ 获取成功！共 {len(data)} 条记录", file=sys.stderr)
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "videos": data,
                    "total": len(data),
                    "pn": pn,
                    "ps": ps
                }
            }
        elif code == -101:
            print("❌ 账号未登录或 Cookie 已失效！请重新扫码。", file=sys.stderr)
            return {"code": -101, "message": "账号未登录或 Cookie 已失效", "data": None}
        else:
            print(f"⚠️ API 返回异常: {result.get('message', 'Unknown Error')} (Code: {code})", file=sys.stderr)
            return {"code": code, "message": result.get("message", "Unknown Error"), "data": None}

    except Exception as e:
        print(f"❌ 请求发生错误: {e}", file=sys.stderr)
        return {"code": -1, "message": str(e), "data": None}


def get_video_url(video_info):
    """
    从单条视频信息生成 B 站完整地址

    Args:
        video_info: 单条视频信息字典

    Returns:
        str: 完整的 B 站视频 URL
    """
    bvid = video_info.get("bvid")
    aid = video_info.get("aid")

    if bvid:
        return f"https://www.bilibili.com/video/{bvid}"
    elif aid:
        return f"https://www.bilibili.com/video/av{aid}"
    else:
        return video_info.get("redirect_link", "未知地址")


def get_video_subtitle(video_info):
    """
    从单条视频信息获取字幕（CC 字幕），不提弹幕

    Args:
        video_info: 单条视频信息字典

    Returns:
        str: 字幕纯文本内容，如果没有字幕返回空字符串
    """
    cookie_str = load_cookie()
    if not cookie_str:
        return ""

    bvid = video_info.get("bvid")
    # cid 可能在顶层，也可能在 page 子对象中
    cid = video_info.get("cid") or video_info.get("page", {}).get("cid")

    if not bvid or not cid:
        print(f"缺少必要参数: bvid={bvid}, cid={cid}", file=sys.stderr)
        return ""

    headers = HEADERS.copy()
    headers["Cookie"] = cookie_str
    headers["Referer"] = "https://www.bilibili.com/"

    try:
        # 1. 获取播放器信息（包含字幕列表）
        player_url = "https://api.bilibili.com/x/player/wbi/v2"
        params = {"bvid": bvid, "cid": cid}

        response = requests.get(player_url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data.get("code") != 0:
            print(f"获取播放器信息失败: {data.get('message')}", file=sys.stderr)
            return ""

        # 2. 提取字幕列表
        subtitles = data.get("data", {}).get("subtitle", {}).get("subtitles", [])

        if not subtitles:
            print(f"视频 {bvid} 没有 CC 字幕", file=sys.stderr)
            return ""

        # 3. 选择第一个字幕（通常是中文或 AI 生成）
        first_sub = subtitles[0]
        sub_url = first_sub.get("subtitle_url", "")

        if not sub_url:
            return ""

        # 补全 URL
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url

        # 4. 下载字幕内容
        sub_response = requests.get(sub_url, headers=headers, timeout=10)
        sub_data = sub_response.json()

        # 5. 提取纯文本（这里已经是字幕正文，不是弹幕）
        body = sub_data.get("body", [])
        if not body:
            return ""

        # 拼接所有字幕文本
        full_text = "\n".join([item.get("content", "") for item in body])

        print(f"成功获取字幕: {first_sub.get('lan_doc', '未知语言')}, 共 {len(body)} 行", file=sys.stderr)
        return full_text

    except Exception as e:
        print(f"获取字幕失败: {e}", file=sys.stderr)
        return ""


def save_history_to_json(history_data, filename="bilibili_history.json"):
    """
    将历史记录保存为 JSON 文件

    Args:
        history_data: fetch_history 返回的字典
        filename: 输出文件名
    """
    if history_data is None:
        print("❌ 无数据可保存")
        return

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    print(f"📁 数据已保存到: {os.path.abspath(filename)}")


def merge_and_dedup(existing_videos, new_videos):
    """
    按视频 URL 去重，合并新旧视频列表。

    - 优先保留已有视频（保留原 subtitle_text 等扩展字段）
    - 新列表中 URL 不在已有集合里的，追加到结果

    Args:
        existing_videos: 已有的视频列表
        new_videos: 新获取的视频列表

    Returns:
        list: 去重合并后的视频列表
    """
    existing_urls = set(get_video_url(v) for v in existing_videos)
    merged = list(existing_videos)
    added = 0
    for video in new_videos:
        url = get_video_url(video)
        if url not in existing_urls:
            merged.append(video)
            added += 1
    print(f"🔄 去重：原有 {len(existing_videos)} 条，新增 {added} 条，合并后共 {len(merged)} 条", file=sys.stderr)
    return merged


def print_help():
    """打印帮助信息"""
    help_text = """\
用法: python3 get_history_byopus.py [选项]

获取 Bilibili 观看历史记录，返回 JSON 格式的原始视频信息，
支持自动获取 CC 字幕并注入到每条记录中。

位置参数:
  pn                页码（从1开始），默认 1
  ps                每页数量，默认 20

选项:
  -o <file.json>    保存到指定 JSON 文件（会自动读取已有文件并按 URL 去重合并）
  -h, --help, help  显示本帮助信息

输出模式:
  - 无 -o: 输出 JSON 到 stdout，progress 信息到 stderr
  - 有 -o: 保存到文件并在终端显示完成信息

字幕说明:
  每条视频记录中会注入 subtitle_text 字段（有字幕=文字，无字幕=""）

示例:
  # 获取第1页10条，输出到终端
  python3 get_history_byopus.py 1 10

  # 获取并保存到文件（自动去重合并）
  python3 get_history_byopus.py 1 20 -o ~/bilibili_history.json

  # 仅查看帮助
  python3 get_history_byopus.py -h
"""
    print(help_text)


def main():
    """主程序：解析命令行参数并获取历史记录"""
    # 解析命令行参数
    # 用法: python3 get_history_byopus.py [pn] [ps] [-o <output.json>]
    pn, ps, output_path = 1, 20, None
    pn_set, ps_set = False, False

    args = [a for a in sys.argv[1:] if a]
    for i, arg in enumerate(args):
        if arg in ("-h", "--help", "help"):
            print_help()
            sys.exit(0)
        elif arg == "-o" and i + 1 < len(args):
            output_path = args[i + 1]
        elif arg.isdigit():
            if not pn_set:
                pn = int(arg)
                pn_set = True
            elif not ps_set:
                ps = int(arg)
                ps_set = True

    # 验证 output_path 必须是 .json 结尾
    if output_path is not None:
        if not output_path.lower().endswith(".json"):
            print(f"❌ 输出文件必须以 .json 结尾: {output_path}")
            sys.exit(1)

    # 获取历史记录
    result = fetch_history(pn, ps)

    if result is None or result.get("data") is None:
        print("❌ 获取历史记录失败")
        sys.exit(1)

    videos = result.get("data", {}).get("videos", [])

    # 为每条视频尝试获取字幕（仅填充 subtitle_text 字段，不改动原始信息）
    print(f"🔄 正在为 {len(videos)} 条视频获取字幕信息...", file=sys.stderr)
    for video in videos:
        sub = get_video_subtitle(video)
        if sub:
            video["subtitle_text"] = sub

    # 构建输出
    output_data = {
        "code": 0,
        "message": "OK",
        "data": {
            "pn": pn,
            "ps": ps,
            "videos": videos,
            "total": len(videos)
        }
    }

    if output_path:
        # 有 -o 参数：读取已有文件，按 URL 去重合并后再写入
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_videos = existing_data.get("data", {}).get("videos", [])
                print(f"🔄 已有 {len(existing_videos)} 条记录，开始去重合并...", file=sys.stderr)
                merged_videos = merge_and_dedup(existing_videos, videos)
                output_data["data"]["videos"] = merged_videos
                output_data["data"]["total"] = len(merged_videos)
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️ 读取已有文件失败，将覆盖写入: {e}", file=sys.stderr)
        save_history_to_json(output_data, output_path)
        print(f"✅ 完成！共 {output_data['data']['total']} 条视频，已保存到: {output_path}")
    else:
        # 无 -o 参数：仅输出 JSON 到 stdout（progress 信息已在 stderr）
        print(json.dumps(output_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()