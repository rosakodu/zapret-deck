# zapret-deck

[🇺🇸 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

一款適用於 Steam Deck 的 Decky Loader 外掛程式，允許您使用 `zapret` (`nfqws`) 策略繞過 DPI 封鎖（YouTube、Discord 等），並透過 `usque` 自動全域路由連接至 **Cloudflare WARP VPN**。

![Screenshot](assets/screenshot.png)

## 📋 功能特點

- **一鍵自動檢測最佳策略**：智慧演算法測試受阻目標，在數秒內自動選擇最有效的策略（如 `ALT`、`FAKE`、`SPLIT`）。
- **便利策略切換**：可視化策略列表，支援取消選擇和手動切換。
- **整合 Cloudflare WARP VPN**：自動註冊 WARP 帳號並提供全流量 TUN 路由（更改 IP 並繞過所有網路封鎖）。
- **原生 Decky Loader 介面**：簡潔清爽，完美契合 Steam Deck 快捷選單風格。
- **開機自啟與狀態儲存**：重啟裝置或在遊戲/桌面模式間切換後，自動恢復服務狀態。
- **極速低耗**：透過 `nfqws` 與 `nftables` 在核心層運行，幾乎零 CPU 與電池消耗。
