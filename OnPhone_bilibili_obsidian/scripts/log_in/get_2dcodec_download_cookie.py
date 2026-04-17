#!/data/data/com.termux/files/usr/bin/python3
import requests
import time
import os
import json

COOKIE_FILE = os.path.expanduser("~/.bili_cookie")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://passport.bilibili.com/",
}

def show_qr(url):
    """用 Python 生成 ASCII 二维码"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1, box_size=1)
        qr.add_data(url)
        qr.print_ascii(invert=True)  # 黑白反转，更易扫描
        return True
    except ImportError:
        return False

def main():
    print("=== Bilibili 扫码登录 ===\n")
    
    # 获取二维码
    r = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers=HEADERS
    )
    data = r.json()["data"]
    key = data["qrcode_key"]
    url = data["url"]
    
    print("请用 Bilibili App 扫描下方二维码：\n")
    
    # 显示二维码
    if not show_qr(url):
        print("未安装 qrcode 库，使用替代方案：")
        print(f"URL: {url}")
        print("\n请手动复制 URL 到在线二维码生成器：")
        print("https://cli.im/url")
    
    print("\n扫码后请在手机上点击确认...\n")
    
    # 轮询
    poll_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    for i in range(60):
        try:
            r = requests.get(f"{poll_url}?qrcode_key={key}", headers=HEADERS)
            result = r.json()
            
            code = result.get("data", {}).get("code", -1)
            
            if code == 0:
                cookies = r.cookies.get_dict()
                if "SESSDATA" in cookies:
                    with open(COOKIE_FILE, "w") as f:
                        f.write(f"SESSDATA={cookies['SESSDATA']}")
                    os.chmod(COOKIE_FILE, 0o600)
                    print(f"\n✓ 登录成功！Cookie 已保存")
                    print(f"位置: {COOKIE_FILE}")
                    return
                else:
                    print(f"\n✗ 无 SESSDATA: {cookies}")
                    return
                    
            elif code == 86038:
                print("❌ 二维码已过期")
                return
            elif code == 86090:
                if i % 2 == 0:
                    print("✓ 已扫码，等待确认...")
            elif code == 86101:
                if i % 5 == 0:
                    print(f"⏳ 等待扫码... ({i*3}秒)")
            else:
                print(f"状态: {code}")
                
        except Exception as e:
            print(f"错误: {e}")
        
        time.sleep(3)
    
    print("\n❌ 超时")

if __name__ == "__main__":
    main()