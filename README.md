# zapret-deck

[🇺🇸 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

A Decky Loader plugin for Steam Deck that allows you to bypass DPI blocks (YouTube, Discord, etc.) using `zapret` (`nfqws`) desync strategies and connect to **Cloudflare WARP VPN** using `usque` with automatic system-wide routing.

![Screenshot](assets/screenshot.png)

## 📋 Features

- **1-Click Strategy Auto-Detection**: Smart testing algorithm checks blocked targets and selects the most effective desync strategy (e.g. `ALT`, `FAKE`, `SPLIT`) in seconds.
- **Easy Strategy Switching**: Interactive strategy list with toggle cancellation and manual selection.
- **Integrated Cloudflare WARP VPN**: Automatic WARP account registration and full-tunnel routing (changes your IP and bypasses all network blocks).
- **Native Decky Loader UI**: Clean, responsive layout seamlessly matching the Steam Deck Quick Access Menu style.
- **Auto-Start & Persistence**: Automatically restores service state after console reboot or switching between Gaming and Desktop modes.
- **High Speed & Low Overhead**: Runs at kernel level via `nfqws` and `nftables`, placing almost zero load on CPU or battery life.

## 📥 Installation

1. Download the latest release (`zapret-deck.zip`) from [Releases](https://github.com/rosakodu/zapret-deck/releases) or build it manually.
2. Copy the ZIP file to your Steam Deck.
3. Enable **Developer Mode** in Steam Settings, then in Decky Loader settings, enable **Developer mode** and choose "Install plugin from file".

## 🚀 How to Use

1. Press the **`...` (Quick Access)** button on your Steam Deck and open the **Decky Loader** tab.
2. Select **Zapret Deck**.
3. Click **"Auto-detect Strategy"**:
   - The plugin tests connections and automatically selects a working strategy (e.g. `ALT`).
   - The **Zapret** toggle will activate.
4. If you need a full VPN, turn on the **WARP** toggle — the plugin will automatically register and route your traffic through Cloudflare WARP.

## ⚖️ License

BSD-3-Clause License.
