# zapret-deck

[🇺🇸 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

一款适用于 Steam Deck 的 Decky Loader 插件，允许您使用 `zapret` (`nfqws`) 策略绕过 DPI 封锁（YouTube、Discord 等），并通过 `usque` 自动全局路由连接至 **Cloudflare WARP VPN**。

![Screenshot](assets/screenshot.png)

## 📋 功能特点

- **一键自动检测最佳策略**：智能算法测试受阻目标，在数秒内自动选择最有效的策略（如 `ALT`、`FAKE`、`SPLIT`）。
- **便捷策略切换**：可视化策略列表，支持取消选择和手动切换。
- **集成 Cloudflare WARP VPN**：自动注册 WARP 账号并提供全流量 TUN 路由（更改 IP 并绕过所有网络封锁）。
- **原生 Decky Loader 界面**：简洁清爽，完美契合 Steam Deck 快捷菜单风格。
- **开机自启与状态保存**：重启设备或在游戏/桌面模式间切换后，自动恢复服务状态。
- **极速低耗**：通过 `nfqws` 与 `nftables` 在内核层运行，几乎零 CPU 与电池消耗。
