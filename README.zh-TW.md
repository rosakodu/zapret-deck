# 🚀 Zapret Deck

[English](README.md) | [Русский](README.ru.md) | [Українська](README.uk.md) | [Türkçe](README.tr.md) | [العربية](README.ar.md) | [فارسی](README.fa.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

---

**Zapret Deck** 是一款專為 **Decky Loader** 設計的強大且易用的外掛程式，旨在繞過網路封鎖（Discord、YouTube 等），並在 **Steam Deck** 以及執行 **SteamOS / Bazzite / ChimeraOS** 的裝置上直接整合 **Cloudflare WARP VPN**。

---

## ✨ 功能特點

- ⚡ **一鍵自動檢測最佳策略**：智慧演算法測試受阻目標，在數秒內自動選擇最有效的解包策略（如 `ALT`、`FAKE`、`SPLIT`）。
- 🎯 **便利策略切換**：可視化策略列表，支援取消選擇和手動切換。
- 🛡 **整合 Cloudflare WARP VPN**：自動註冊 WARP 帳號並提供全流量 TUN 路由（更改 IP 並繞過所有網路封鎖）。
- 🎨 **原生 Decky Loader 介面**：簡潔清爽，完美契合 Steam Deck 快捷選單風格。
- 🔄 **開機自啟與狀態儲存**：重啟裝置或在遊戲/桌面模式間切換後，自動恢復服務狀態。
- 🚀 **極速低耗**：透過 `nfqws` 與 `nftables` 在核心層運行，幾乎零 CPU 與電池消耗。

---

## 🛠 系統要求

- **Steam Deck** (LCD 或 OLED) / 執行 **SteamOS 3.x / Bazzite / ChimeraOS / Nobara** 的裝置。
- 已安裝 **[Decky Loader](https://decky.realm3.org/)**。

---

## 📦 安裝說明

### 方法一：透過 Decky Loader 介面安裝 (ZIP)

1. 在 GitHub 的 **Releases** 頁面下載最新版本的 `zapret-deck.zip`。
2. 打開 **Decky Loader** -> *設定 (Settings)* -> *開發者 (Developer)*。
3. 點擊 **Install Plugin from ZIP** 並選擇 `zapret-deck.zip`。

### 方法二：透過終端機手動安裝 (SSH / Konsole)

在 Steam Deck 終端機執行以下命令：

```bash
curl -sSL https://github.com/rosakodu/zapret-deck/releases/download/v1.0.0/zapret-deck.zip -o /tmp/zapret-deck.zip && \
sudo mkdir -p /home/deck/homebrew/plugins && \
sudo unzip -o /tmp/zapret-deck.zip -d /home/deck/homebrew/plugins/ && \
sudo chmod +x /home/deck/homebrew/plugins/zapret-deck/bin/* && \
sudo systemctl restart plugin_loader.service
```

---

## ⚖️ 開源協定

基於 **BSD-3-Clause** 協定開源。
