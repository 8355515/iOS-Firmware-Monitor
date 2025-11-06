# iOS Firmware Monitor

自动监控 iOS 固件版本（低于 26.0），发现新固件时通过 Telegram 推送通知。

## 🔧 使用步骤

1. Fork 或创建此仓库
2. 在 Settings → Secrets → Actions 中添加：
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. GitHub Actions 会每小时自动运行
4. 新固件出现时会收到 Telegram 通知
