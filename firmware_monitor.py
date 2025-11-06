import requests
import json
import os

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 上次通知记录
RECORD_FILE = "last_firmware.json"

# 设备代号列表，可根据需求修改
DEVICE_LIST = ["iPhone15,2", "iPhone15,3", "iPhone14,2"]

# 代号 -> 机型名称映射
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

def get_firmwares(device):
    url = f"https://api.ipsw.me/v4/device/{device}?type=ipsw"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"⚠️ 获取 {device} 固件失败: {resp.status_code}")
        return []
    return resp.json().get("firmwares", [])

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def load_last_record():
    if not os.path.exists(RECORD_FILE):
        return {}
    with open(RECORD_FILE, "r") as f:
        return json.load(f)

def save_record(record):
    with open(RECORD_FILE, "w") as f:
        json.dump(record, f)

def main():
    last_record = load_last_record()
    new_record = {}
    notify_msgs = []

    for device in DEVICE_LIST:
        firmwares = get_firmwares(device)
        # 只监控 iOS < 26 的固件
        new_versions = [fw for fw in firmwares if float(fw["version"].split(".")[0]) < 26.0]
        latest = new_versions[0]["version"] if new_versions else None

        device_name = DEVICE_NAMES.get(device, device)

        if latest and last_record.get(device) != latest:
            msg = f"📱 *{device_name}* 发现新固件：`{latest}`\n🔗 [下载链接]({new_versions[0]['url']})"
            notify_msgs.append(msg)
            new_record[device] = latest
        else:
            new_record[device] = last_record.get(device, latest)

    if notify_msgs:
        send_telegram("\n\n".join(notify_msgs))
        print("✅ 已发送 Telegram 通知。")
    else:
        print("ℹ️ 无新固件。")

    save_record(new_record)

if __name__ == "__main__":
    main()
