#!/usr/bin/env python3
# monitor.py
# 自动从爱思助手获取所有设备固件签名状态，检测 iOS < 26.0 的签名固件
# 通过 Telegram Bot 推送新签名固件通知
# 从环境变量读取 TG_BOT_TOKEN 和 TG_CHAT_ID（建议使用 GitHub Secrets）

import json
import os
import requests
import time
from packaging import version
from pathlib import Path

MIN_VERSION = version.parse("26.0")
DATA_FILE = Path("last_notified.json")

TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

HEADERS = {
    "User-Agent": "ios-firmware-monitor/1.0 (+https://github.com)"
}

def send_telegram(msg: str):
    """发送 Telegram 通知（会在环境变量中读取 token & chat id）"""
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID（从环境变量读取）")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=10, headers=HEADERS)
        if resp.status_code != 200:
            print(f"[Telegram] 非 200 响应: {resp.status_code} {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"[Telegram Error] {e}")
        return False

def load_last() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Error] 读取 {DATA_FILE} 失败: {e}")
            return {}
    return {}

def save_last(data: dict):
    try:
        DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Error] 保存 {DATA_FILE} 失败: {e}")

def get_all_devices() -> dict:
    """
    从爱思助手获取所有设备列表（返回 dict: device_id -> device_name）
    接口: https://api.i4.cn/firmware/getAllDeviceList
    """
    url = "https://api.i4.cn/firmware/getAllDeviceList"
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Error] 获取设备列表失败: {e}")
        return {}
    devices = {}
    for cat in data.get("data", []):
        for d in cat.get("deviceList", []):
            devices[d.get("device")] = d.get("name")
    return devices

def get_signed_firmwares(device: str) -> list:
    """
    获取某个设备的固件信息，并筛选出 isSign == 1 且版本 < MIN_VERSION 的条目
    """
    url = f"https://api.i4.cn/firmware/deviceData?device={device}"
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Error] 获取 {device} 固件失败: {e}")
        return []
    firmwares = data.get("firmwares", [])
    out = []
    for f in firmwares:
        ver = f.get("version")
        is_sign = f.get("isSign")
        try:
            if ver and is_sign == 1 and version.parse(ver) < MIN_VERSION:
                out.append({"version": ver, "info": f})
        except Exception:
            # 忽略无法解析的版本字符串
            continue
    return out

def chunked_iter(items, size):
    it = iter(items)
    while True:
        chunk = []
        try:
            for _ in range(size):
                chunk.append(next(it))
        except StopIteration:
            if chunk:
                yield chunk
            break
        yield chunk

def main():
    print("🚀 ios-firmware-monitor 启动")
    devices = get_all_devices()
    if not devices:
        print("❌ 未能获取设备列表，退出。")
        return
    print(f"📱 共找到设备: {len(devices)}")

    last = load_last()
    new_last = {}
    updates = []

    # 为避免一次性请求过多，分块处理（可调节）
    device_items = list(devices.items())

    for idx, (dev, name) in enumerate(device_items, start=1):
        print(f"[{idx}/{len(device_items)}] 检查: {name} ({dev})")
        firmwares = get_signed_firmwares(dev)
        versions = [f["version"] for f in firmwares]
        old = set(last.get(dev, []))
        new = sorted(set(versions) - old, key=lambda s: version.parse(s))
        if new:
            lines = [f"📢 *{name}*（{dev}）检测到新签名固件："]
            for v in new:
                lines.append(f"- iOS {v}")
            msg = "\n".join(lines)
            print(msg)
            ok = send_telegram(msg)
            if ok:
                updates.append({"device": dev, "name": name, "versions": new})
        else:
            print(f"✅ {name} 无新签名固件")
        new_last[dev] = versions
        # sleep to prevent rate limiting
        time.sleep(1.0)

    save_last(new_last)
    if updates:
        print(f"✅ 共推送 {len(updates)} 条更新")
    else:
        print("😴 没有新的签名固件变动")

if __name__ == '__main__':
    main()
