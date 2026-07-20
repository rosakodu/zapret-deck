# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

A standalone Decky Loader plugin for Steam Deck that combines DPI bypass via **Zapret** (nfqws) and a secure VPN tunnel via **Cloudflare WARP (MASQUE protocol)** — bypassing internet censorship and throttling (including YouTube and Discord) natively in gaming mode, without any external applications.

![Screenshot](assets/screenshot.png)

## 📋 Features

- **Two Bypass Modes**: Switch between **Zapret (DPI Bypass)** for direct unthrottled access (best for YouTube 4K / Discord) and **WARP VPN (MASQUE)** for full tunnel VPN.
- **MASQUE Protocol**: WARP connects via MASQUE (HTTP/3 over QUIC), which is indistinguishable from regular HTTPS traffic.
- **Auto-detect Strategy**: Zapret features built-in automatic strategy detection — it tests and selects the best DPI bypass parameters for your ISP.
- **Blocked Domain Manager**: Add and manage domains to bypass, directly from the plugin UI.
- **100% Standalone**: Runs in userspace. No kernel module compilation, no disabling SteamOS read-only filesystem, no dkms.

## 📥 Installation

1. Download the latest release (`zapret-deck.zip`) from the [Releases](https://github.com/rosakodu/zapret-deck/releases) page.
2. Transfer the ZIP archive to your Steam Deck.
3. Enable **Developer Mode** in Steam Deck System Settings.
4. In Decky Loader settings, enable Developer mode and select "Install plugin from file" (or drag and drop the ZIP).

## 🚀 How to Use

### 1. Zapret (DPI Bypass)
Select **Zapret (DPI Bypass)** in the plugin mode dropdown.
- Click **Auto-detect Strategy** to automatically test and apply the best bypass strategy for your network.
- Use **Edit Blocked Hostlist** to add specific domains (e.g. `youtube.com`).

### 2. WARP VPN (MASQUE)
Select **WARP (MASQUE VPN)** in the plugin mode dropdown.
- On first run, click **Generate WARP Account** to register a new client profile.
- The plugin will automatically connect via MASQUE (HTTP/3) and establish an encrypted tunnel.

## ⚖️ Credits and Sources

This plugin is built using the following open-source projects:

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — open-source Cloudflare WARP MASQUE client.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — the powerful DPI bypass engine `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — original DPI bypass strategies for YouTube and Discord.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — Linux shell configuration and autotuning logic.

## ⚖️ License
BSD-3-Clause
