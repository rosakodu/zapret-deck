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

## 📥 安裝說明

1. 從 [Releases](https://github.com/rosakodu/zapret-deck/releases) 頁面下載最新版本（`zapret-deck.zip`）或手動建置。
2. 將 ZIP 檔案複製到您的 Steam Deck。
3. 在 Steam 設定中啟用 **開發者模式**，然後在 Decky Loader 設定中啟用 **Developer mode** 並選擇「從檔案安裝外掛程式」。

## 🚀 使用方法

1. 按下 Steam Deck 上的 **`...`（快捷選單）** 按鈕並打開 **Decky Loader** 標籤頁。
2. 選擇 **Zapret Deck**。
3. 點擊 **「自動檢測策略」**：
   - 外掛程式將測試連接並自動選擇可用的策略（如 `ALT`）。
   - **Zapret** 開關將被啟用。
4. 如果需要完整 VPN，開啟 **WARP** 開關 — 外掛程式將自動註冊並透過 Cloudflare WARP 路由您的流量。

## ⚖️ 開源協定

BSD-3-Clause License.
