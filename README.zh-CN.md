# 🚀 Zapret Deck

🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md) | 🇺🇦 [Українська](README.uk.md) | 🇹🇷 [Türkçe](README.tr.md) | 🇸🇦 [العربية](README.ar.md) | 🇮🇷 [فارسی](README.fa.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-TW.md)

---

<p align="center">
  <img src="assets/screenshot.png" alt="Zapret Deck Screenshot" width="650"/>
</p>

---

**Zapret Deck** 是一款专为 **Decky Loader** 设计的强大且易用的插件，旨在绕过网络封锁（Discord、YouTube 等），并在 **Steam Deck** 以及运行 **SteamOS / Bazzite / ChimeraOS** 的设备上直接集成 **Cloudflare WARP VPN**。

---

## ✨ 功能特点

- ⚡ **一键自动检测最佳策略**：智能算法测试受阻目标，在数秒内自动选择最有效的解包策略（如 `ALT`、`FAKE`、`SPLIT`）。
- 🎯 **便捷策略切换**：可视化策略列表，支持取消选择和手动切换。
- 🛡 **集成 Cloudflare WARP VPN**：自动注册 WARP 账号并提供全流量 TUN 路由（更改 IP 并绕过所有网络封锁）。
- 🎨 **原生 Decky Loader 界面**：简洁清爽，完美契合 Steam Deck 快捷菜单风格。
- 🔄 **开机自启与状态保存**：重启设备或在游戏/桌面模式间切换后，自动恢复服务状态。
- 🚀 **极速低耗**：通过 `nfqws` 与 `nftables` 在内核层运行，几乎零 CPU 与电池消耗。

---

## 🛠 系统要求

- **Steam Deck** (LCD 或 OLED) / 运行 **SteamOS 3.x / Bazzite / ChimeraOS / Nobara** 的设备。
- 已安装 **[Decky Loader](https://decky.realm3.org/)**。

---

## 📦 安装说明

### 方法一：通过 Decky Loader 界面安装 (ZIP)

1. 在 GitHub 的 **Releases** 页面下载最新版本的 `zapret-deck.zip`。
2. 打开 **Decky Loader** -> *设置 (Settings)* -> *开发者 (Developer)*。
3. 点击 **Install Plugin from ZIP** 并选择 `zapret-deck.zip`。

### 方法二：通过终端手动安装 (SSH / Konsole)

在 Steam Deck 终端执行以下命令：

```bash
curl -sSL https://github.com/rosakodu/zapret-deck/releases/download/v1.0.0/zapret-deck.zip -o /tmp/zapret-deck.zip && \
sudo mkdir -p /home/deck/homebrew/plugins && \
sudo unzip -o /tmp/zapret-deck.zip -d /home/deck/homebrew/plugins/ && \
sudo chmod +x /home/deck/homebrew/plugins/zapret-deck/bin/* && \
sudo systemctl restart plugin_loader.service
```

---

## ⚖️ 开源协议

基于 **BSD-3-Clause** 协议开源。
