# 🍎 iOS Firmware Auto Monitor  
> 自动监控多个 iPhone / iPad 固件版本变化（低于 iOS 26.0 的可降级固件），并通过 **Telegram Bot** 自动推送提醒。  
数据源使用官方 [api.ipsw.me](https://api.ipsw.me/v4/)，全球可访问，兼容 **GitHub Actions** 自动运行。

---

## 🚀 功能简介

✅ 自动获取 Apple 官方固件版本（通过 [ipsw.me API](https://api.ipsw.me/)）  
✅ 监控多个 iPhone / iPad 设备型号  
✅ 检测低于 iOS 26.0 的固件更新  
✅ 通过 Telegram Bot 推送更新提醒  
✅ GitHub Actions 每小时自动运行  
✅ 自动记录上次推送，防止重复通知 
✅ 通知语言为中文
✅ 汇总推送（一次性报告所有设备） 
✅ 无可降级固件时提示：  
> ⚠️ 当前未发现任何可降级固件通道

---

## 🧩 文件结构

```
ios-firmware-monitor/
├── .github/
│   └── workflows/
│       └── monitor.yml        # GitHub Actions 定时任务
├── monitor.py                 # 主程序
├── requirements.txt           # Python依赖
├── last_firmware.json         # 自动生成的固件记录文件
└── README.md                  # 说明文档
```

---

## ⚙️ 部署教程

### 🪶 1. Fork 本仓库 或 自建新仓库

- 点击右上角的 **“Fork”** 按钮复制此项目  
- 或新建仓库后上传文件（包括 `.github/workflows/monitor.yml`）

---

### 🤖 2. 创建 Telegram Bot

1. 打开 Telegram，搜索并进入 [@BotFather](https://t.me/BotFather)  
2. 发送命令 `/newbot`  
3. 根据提示设置名称与用户名  
4. BotFather 会返回类似这样的信息：
   ```
   Done! Congratulations on your new bot.
   Use this token to access the HTTP API:
   123456789:AAExampleToken
   ```
5. 复制这个 **Bot Token**，稍后在 GitHub Secrets 中配置。

---

### 💬 3. 获取你的 Chat ID

1. 打开 Telegram，搜索 [@userinfobot](https://t.me/userinfobot)  
2. 发送任意消息  
3. 它会返回类似：
   ```
   Your user ID: 987654321
   ```
4. 记录下这个数字（Chat ID）

---

### 🔐 4. 设置 GitHub Secrets

打开你的仓库 →  
`Settings` → `Secrets and variables` → `Actions` → `New repository secret`  

添加以下两项：

| 名称 | 示例值 | 说明 |
|------|---------|------|
| `TG_BOT_TOKEN` | `123456789:AAExampleToken` | Telegram BotFather 提供的 Token |
| `TG_CHAT_ID` | `987654321` | 你在 @userinfobot 中获取的 ID |

---

### 🕐 5. GitHub Actions 定时任务

此项目的 `.github/workflows/monitor.yml` 已预设：

```yaml
on:
  schedule:
    - cron: "0 * * * *"   # 每小时运行一次
  workflow_dispatch:       # 支持手动触发
```

> 🧭 意味着 GitHub 会 **每整点自动运行一次** 脚本检查固件更新。

---

### 🧰 6. 手动运行一次测试

1. 进入仓库页面  
2. 点击上方标签栏 **“Actions”**  
3. 选择左侧工作流 `iOS Firmware Monitor`  
4. 点击 “Run workflow” → 确认执行  

执行完成后，如果配置正确，你会在 Telegram 收到推送：

```
📱 iPhone15,2 发现新固件：18.7
🔗 下载链接：https://updates.cdn-apple.com/...
```

---

## 🧩 自定义设置

### 📱 修改监控设备
在 `firmware_monitor.py` 中找到：

```python
DEVICE_LIST = ["iPhone15,2", "iPhone14,2"]
```

可以修改为：

```python
DEVICE_LIST = ["iPhone14,5", "iPad13,1"]
```

> ✅ 支持所有 Apple 设备，可从 [ipsw.me/products](https://ipsw.me/products) 查询型号。

---

### ⚙️ 修改检测条件

若要监控所有版本（不限定 iOS 26 以下），修改：

```python
new_versions = [fw for fw in firmwares if float(fw["version"].split(".")[0]) < 26.0]
```
为：
```python
new_versions = firmwares
```

---

### 💾 关于记录文件

- `last_firmware.json` 用于存储上次通知的固件版本  
- 每次运行自动更新  
- GitHub Actions 自动提交更新到仓库

---

## 🧑‍💻 本地调试

在本地测试：

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="你的BotToken"
export TELEGRAM_CHAT_ID="你的ChatID"
python firmware_monitor.py
```

---

## 🕒 Cron 时间说明

| 表达式 | 含义 |
|--------|------|
| `0 * * * *` | 每小时运行一次 |
| `*/30 * * * *` | 每 30 分钟运行一次 |
| `0 0 * * *` | 每天 00:00 运行一次 |

> GitHub 的 Cron 基于 UTC 时间。

---

## 🧾 常见问题

**Q:** 没收到通知？  
✅ 检查 Bot Token 与 Chat ID 是否正确  
✅ 确保 Bot 已与你开启对话  
✅ 查看 Actions 日志确认是否成功运行  

**Q:** 支持哪些设备？  
✅ 所有 [ipsw.me](https://ipsw.me/) 上的设备型号均可监控  

---

## 📬 示例通知

```
📱 iPhone14,2 发现新固件：18.6.1
🔗 下载链接：https://updates.cdn-apple.com/2024Spring/...
```

---

## 🏁 完成！

当 Apple 发布新固件（例如 iOS 18.7、18.8）时，Telegram 机器人将第一时间通知你 🎉

---

MIT License © 2025
