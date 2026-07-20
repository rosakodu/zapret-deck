# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

一款獨立的 Steam Deck Decky Loader 插件，結合了通過 **Zapret**（nfqws）的 DPI 繞過和通過 **Cloudflare WARP（MASQUE 協議）**的安全 VPN 隧道 — 無需任何外部應用程式，直接在遊戲模式下繞過網際網路審查和限速（包括 YouTube 和 Discord）。

> **注意：** 此插件完全獨立。無需安裝 Amnezia VPN、warp-cli 或任何桌面 GUI 管理器。所有二進位檔案均已內建。

![截圖](assets/screenshot.png)

## 📋 功能

- **兩種繞過模式**：在 **Zapret（DPI 繞過）**（最佳用於 YouTube 4K/Discord）和 **WARP VPN（MASQUE）**全隧道 VPN 之間切換。
- **MASQUE 協議**：WARP 通過 MASQUE（HTTP/3 over QUIC）連接，與普通 HTTPS 流量無法區分。
- **自動偵測策略**：Zapret 自動測試並選擇適合您 ISP 的最佳 DPI 繞過參數。
- **網域管理員**：直接從插件 UI 新增和管理要繞過的網域。
- **100% 獨立**：在使用者空間執行，無需編譯核心模組。

## 📥 安裝

1. 從 [Releases](https://github.com/rosakodu/zapret-deck/releases) 頁面下載最新版本（`zapret-deck.zip`）。
2. 將 ZIP 壓縮包傳輸到您的 Steam Deck。
3. 在 Steam Deck 系統設定中啟用**開發者模式**。
4. 在 Decky Loader 設定中啟用開發者模式，然後選擇「從檔案安裝插件」。

## ⚖️ 致謝與來源

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — 開源 Cloudflare WARP MASQUE 用戶端。
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — 強大的 DPI 繞過引擎 `nfqws`。
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — YouTube 和 Discord 的原始 DPI 繞過策略。
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — Linux Shell 設定和自動調整邏輯。

## ⚖️ 授權
BSD-3-Clause
