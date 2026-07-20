# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

一款独立的 Steam Deck Decky Loader 插件，结合了通过 **Zapret**（nfqws）的 DPI 绕过和通过 **Cloudflare WARP（MASQUE 协议）**的安全 VPN 隧道 — 无需任何外部应用程序，直接在游戏模式下绕过互联网审查和限速（包括 YouTube 和 Discord）。

> **注意：** 此插件完全独立。无需安装 Amnezia VPN、warp-cli 或任何桌面 GUI 管理器。所有二进制文件均已内置。

![截图](assets/screenshot.png)

## 📋 功能

- **两种绕过模式**：在 **Zapret（DPI 绕过）**（最佳用于 YouTube 4K/Discord）和 **WARP VPN（MASQUE）**全隧道 VPN 之间切换。
- **MASQUE 协议**：WARP 通过 MASQUE（HTTP/3 over QUIC）连接，与普通 HTTPS 流量无法区分。
- **自动检测策略**：Zapret 自动测试并选择适合您 ISP 的最佳 DPI 绕过参数。
- **域名管理器**：直接从插件 UI 添加和管理要绕过的域名。
- **100% 独立**：在用户空间运行，无需编译内核模块。

## 📥 安装

1. 从 [Releases](https://github.com/rosakodu/zapret-deck/releases) 页面下载最新版本（`zapret-deck.zip`）。
2. 将 ZIP 压缩包传输到您的 Steam Deck。
3. 在 Steam Deck 系统设置中启用**开发者模式**。
4. 在 Decky Loader 设置中启用开发者模式，然后选择"从文件安装插件"。

## ⚖️ 鸣谢与来源

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — 开源 Cloudflare WARP MASQUE 客户端。
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — 强大的 DPI 绕过引擎 `nfqws`。
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — YouTube 和 Discord 的原始 DPI 绕过策略。
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — Linux Shell 配置和自动调整逻辑。

## ⚖️ 许可证
BSD-3-Clause
