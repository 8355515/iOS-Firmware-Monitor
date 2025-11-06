#!/usr/bin/env python3
# monitor.py - 爱思助手固件签名监控 v3
# 特性：汇总多设备通知、无固件时发送统一提示、保留防重复通知逻辑、包含更新时间

import json
import os
import requests
import time
from packaging import version
from pathlib import Path
from datetime import datetime

# 确保脚本工作目录为脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

MIN_VERSION = version.parse("26.0")
DATA_FILE = Path("last_notified.json")

TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

HEADERS = {
    "User-Agent": "ios-firmware-monitor/3.0 (+https://github.com)"
}

def send_telegram(msg: str):
    """发送 Telegram 通知"""
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("❌ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID（从环境变量读取）")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=15, headers=HEADERS)
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
    """从爱思助手获取所有设备列表"""
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
    """获取设备签名固件（仅保留 iOS < MIN_VERSION 且 isSign == 1）"""
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
                out.append(ver)
        except Exception:
            continue
    return out

def build_report(devices_results: dict, timestamp: str) -> str:
    """构建汇总报告消息（Markdown）"""
    title = "📢 iOS 固件签名监控报告"
    lines = [title, "", f"更新时间：{timestamp}", ""]
    any_open = False
    for dev, info in sorted(devices_results.items(), key=lambda x: x[0]):
        name = info.get("name", dev)
        versions = info.get("new_versions", [])
        if versions:
            any_open = True
            ver_list = ", ".join([f"iOS {v}" for v in sorted(versions, key=lambda s: version.parse(s))])
            lines.append(f"✅ {name}（{dev}） — 可降级固件：{ver_list}")
        else:
            lines.append(f"⚠️ {name}（{dev}） — 未发现可降级固件")
    lines.append("")
    if not any_open:
        lines = [title, "", f"⚠️ 当前未发现任何可降级固件通道", "", f"更新时间：{timestamp}"]
    return "\n".join(lines)

def main():
    print("🚀 ios-firmware-monitor v3 启动")
    print(f"当前工作目录: {os.getcwd()}")

    # 确保记录文件存在
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
        print("🆕 创建 last_notified.json")

    devices = get_all_devices()
    if not devices:
        print("❌ 未能获取设备列表，退出。")
        return
    print(f"📱 共找到设备: {len(devices)}")

    last = load_last()
    new_last = {}
    devices_results = {}

    for idx, (dev, name) in enumerate(devices.items(), start=1):
        print(f"[{idx}/{len(devices)}] 检查: {name} ({dev})")
        firmwares = get_signed_firmwares(dev)
        old = set(last.get(dev, []))
        new = sorted(set(firmwares) - old, key=lambda s: version.parse(s))
        devices_results[dev] = {"name": name, "new_versions": new, "all_signed": firmwares}
        new_last[dev] = firmwares
        time.sleep(0.8)

    # 构建并发送汇总消息
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(devices_results, timestamp)
    print("---- Report ----")
    print(report)
    send_telegram(report)

    # 仅在脚本结束后一次性保存记录（防止中间多次写）
    save_last(new_last)
    print("📂 保存 last_notified.json 完成")

if __name__ == '__main__':
    main()
