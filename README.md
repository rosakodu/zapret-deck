# 🚀 Zapret Deck

🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md) | 🇺🇦 [Українська](README.uk.md) | 🇹🇷 [Türkçe](README.tr.md) | 🇸🇦 [العربية](README.ar.md) | 🇮🇷 [فارسی](README.fa.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-TW.md)

---

<p align="center">
  <img src="assets/screenshot.png" alt="Zapret Deck Screenshot" width="650"/>
</p>

---

**Zapret Deck** is a powerful and easy-to-use plugin for **Decky Loader** designed to bypass network restrictions (Discord, YouTube, etc.) and integrate **Cloudflare WARP VPN** directly into the **Steam Deck** interface and devices running **SteamOS / Bazzite / ChimeraOS**.

---

## ✨ Features

- ⚡ **1-Click Strategy Auto-Detection**: Smart testing algorithm checks blocked targets and selects the most effective desync strategy (e.g. `ALT`, `FAKE`, `SPLIT`) in seconds.
- 🎯 **Easy Strategy Switching**: Interactive strategy list with toggle cancellation and manual selection.
- 🛡 **Integrated Cloudflare WARP VPN**: Automatic WARP account registration and full-tunnel routing (changes your IP and bypasses all network blocks).
- 🎨 **Native Decky Loader UI**: Clean, responsive layout seamlessly matching the Steam Deck Quick Access Menu style.
- 🔄 **Auto-Start & Persistence**: Automatically restores service state after console reboot or switching between Gaming and Desktop modes.
- 🚀 **High Speed & Low Overhead**: Runs at kernel level via `nfqws` and `nftables`, placing almost zero load on CPU or battery life.

---

## 🛠 Requirements

- **Steam Deck** (LCD or OLED) / PC running **SteamOS 3.x / Bazzite / ChimeraOS / Nobara**.
- Installed **[Decky Loader](https://decky.realm3.org/)**.

---

## 📦 Installation

### Option 1. Automatic via Decky Loader (ZIP)

1. Open the **Releases** section on GitHub and download `zapret-deck.zip` from the latest release (`v1.0.0`).
2. Open **Decky Loader** -> *Settings* -> *Developer*.
3. Click **Install Plugin from ZIP** and select `zapret-deck.zip`.
4. Restart Decky Loader if prompted.

### Option 2. Manual via Terminal (SSH / Konsole)

Run this single command on your Steam Deck:

```bash
curl -sSL https://github.com/rosakodu/zapret-deck/releases/download/v1.0.0/zapret-deck.zip -o /tmp/zapret-deck.zip && \
sudo mkdir -p /home/deck/homebrew/plugins && \
sudo unzip -o /tmp/zapret-deck.zip -d /home/deck/homebrew/plugins/ && \
sudo chmod +x /home/deck/homebrew/plugins/zapret-deck/bin/* && \
sudo systemctl restart plugin_loader.service
```

---

## 🎮 How to Use

1. Press the **`...` (Quick Access)** button on your Steam Deck and open the **Decky Loader** tab.
2. Select **Zapret Deck**.
3. Click **"Auto-detect Strategy"**:
   - The plugin tests connections and automatically selects a working strategy (`ALT`).
   - You will see a completion toast, and **Zapret Bypass** will turn blue and display **"Active"**.
4. If you need a full VPN, toggle **WARP** — the plugin will automatically register with Cloudflare and route your traffic.

---

## 📂 Project Structure

- `main.py` — Python plugin backend (RPC calls, settings persistence).
- `src/index.tsx` — React & TypeScript UI for Decky Loader.
- `py_modules/zapret_deck/`:
  - `zapret_manager.py` — `nfqws` daemon and `nftables` rule management.
  - `warp_manager.py` — `usque` client and `warp0` TUN routing management.
  - `strategies.py` — Preset DPI bypass strategies.
- `bin/` — Compiled binaries (`nfqws`, `usque`).

---

## ⚖️ License

Distributed under the **BSD-3-Clause** license. See LICENSE for details.
