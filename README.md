# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md)

A standalone plugin for Decky Loader on Steam Deck that combines DPI bypass via **Zapret** (nfqws) and secure VPN tunnel via **Cloudflare WARP (MASQUE protocol)** to bypass local internet censorship and throttling (including YouTube and Discord) natively in gaming mode.

> **Note:** This plugin is 100% standalone and does not require any external applications (like Amnezia VPN, warp-cli, or desktop GUI managers) to be installed on your Steam Deck. All binaries are bundled inside.

## 📋 Features

- **Double Protection**: Choose between **Zapret (DPI Bypass)** for direct, unthrottled access (best for YouTube 4K/Discord) or **WARP VPN (MASQUE)** for full-tunnel security.
- **MASQUE Protocol**: WARP is established via the MASQUE (HTTP/3 over QUIC) protocol, which natively bypasses standard WireGuard handshake blocks and DPI tracking in restricted network regions.
- **Auto-detection**: Zapret features a built-in strategy picker that automatically tests and selects the best desynchronization parameters for your ISP.
- **Blocked Hostlist Manager**: Add and manage domains to be bypassed directly from the plugin UI.
- **100% Standalone**: Userspace execution. Does not require disabling SteamOS read-only filesystem, compiling kernel modules, or configuring dkms.

## 📥 Installation

1. Download the latest release (`zapret-deck.zip`) from the [Releases](https://github.com/rosakodu/zapret-deck/releases) page.
2. Transfer the ZIP archive to your Steam Deck.
3. Enable **Developer Mode** in Steam Deck System Settings.
4. In Decky Loader settings, go to the Developer section, enable **Developer mode**, and select "Install plugin from file" (or drag and drop the ZIP).

## 🚀 How to Use

### 1. Zapret (DPI Bypass)
Select **Zapret (DPI Bypass)** in the plugin mode dropdown.
- Click **Auto-detect Strategy** to run tests and find the best working strategy for your network.
- Use the **Edit Blocked Hostlist** button to add specific domains you want to bypass (e.g. `youtube.com`).

### 2. WARP VPN (MASQUE)
Select **WARP (MASQUE VPN)** in the plugin mode dropdown.
- If using for the first time, click **Generate WARP Account** to register a new client profile.
- The plugin will automatically connect via MASQUE (HTTP/3) and establish a secure, unblocked VPN tunnel.

## ⚖️ Credits and Sources

This plugin is built using the following open-source projects and contributions:

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — for the lightweight open-source Cloudflare WARP MASQUE client.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — for the powerful DPI bypass engine `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — for the original DPI desynchronization strategies.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — for Linux shell configuration and autotuning logic.

## ⚖️ License
This project is licensed under the BSD-3-Clause License.
