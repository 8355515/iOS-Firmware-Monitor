import requests
import json
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RECORD_FILE = "last_firmware.json"
DEVICE_LIST = ["iPhone15,2", "iPhone14,2"]

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
        new_versions = [fw for fw in firmwares if float(fw["version"].split(".")[0]) < 26.0]
        latest = new_versions[0]["version"] if new_versions else None

        if latest and last_record.get(device) != latest:
            msg = f"📱 *{device}* 发现新固件：`{latest}`\n🔗 [下载链接]({new_versions[0]['url']})"
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
