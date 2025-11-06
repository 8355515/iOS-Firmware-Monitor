
# iOS Firmware Monitor v1

import requests, json, os
from datetime import datetime

# Telegram Bot 配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 监控设备
DEVICE_LIST = ["iPhone15,2", "iPhone15,3", "iPhone14,2"]
DEVICE_NAMES = {
    "iPhone10,1": "iPhone 8",
    "iPhone10,2": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X",
    "iPhone10,4": "iPhone 8",
    "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,6": "iPhone X",
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max",
    "iPhone11,8": "iPhone XR",
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",
    "iPhone13,1": "iPhone 12 mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone16,1": "iPhone 15",
    "iPhone16,2": "iPhone 15 Plus",
    "iPhone16,3": "iPhone 15 Pro",
    "iPhone16,4": "iPhone 15 Pro Max",
}

# 上次通知文件
LAST_FILE = "last_notified.json"
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_notified = json.load(f)
else:
    last_notified = {}

def get_firmwares(device):
    url = f"https://api.ipsw.me/v4/device/{device}?type=ipsw"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        firmwares = []
        for fw in data.get("firmwares", []):
            version = fw.get("version")
            if version and float(version.split(".")[0]) < 26.0 and fw.get("signed"):
                firmwares.append(version)
        return sorted(set(firmwares))
    except Exception as e:
        print(f"❌ 获取 {device} 数据失败: {e}")
        return []

def send_telegram_message(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("⚠️ 未设置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过发送。")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"⚠️ Telegram 发送失败: {res.text}")
    except Exception as e:
        print(f"❌ Telegram 发送异常: {e}")

def main():
    print("🚀 iOS Firmware Monitor v1 启动")
    summary = []
    updated = False

    for device in DEVICE_LIST:
        name = DEVICE_NAMES.get(device, device)
        firmwares = get_firmwares(device)

        if firmwares:
            latest = firmwares[-1]
            last = last_notified.get(device)
            if last != latest:
                summary.append(f"✅ {name} — 可降级固件: iOS {latest}")
                last_notified[device] = latest
                updated = True
            else:
                summary.append(f"ℹ️ {name} — 无新降级固件 (当前 iOS {latest})")
        else:
            summary.append(f"⚠️ {name} — 未发现可降级固件")

    if not updated and all("⚠️" in line or "ℹ️" in line for line in summary):
        message = "📢 iOS 固件签名监控报告\n\n⚠️ 当前未发现任何可降级固件通道"
    else:
        message = "📢 iOS 固件签名监控报告\n\n" + "\n".join(summary)

    message += f"\n\n更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print(message)
    send_telegram_message(message)

    with open(LAST_FILE, "w", encoding="utf-8") as f:
        json.dump(last_notified, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
