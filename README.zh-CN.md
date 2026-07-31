# zapret-deck

[🇺🇸 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

一款适用于 Steam Deck 的 Decky Loader 插件，允许您使用 `zapret` (`nfqws`) 策略绕过 DPI 封锁（YouTube、Discord 等），并通过 `usque` 自动全局路由连接至 **Cloudflare WARP VPN**。

![Screenshot](assets/screenshot.png)

## 📋 功能特点

- **一键自动检测最佳策略**：智能算法测试受阻目标，在数秒内自动选择最有效的策略（如 `ALT`、`FAKE`、`SPLIT`）。
- **便捷策略切换**：可视化策略列表，支持取消选择和手动切换。
- **集成 Cloudflare WARP VPN**：自动注册 WARP 账号并提供全流量 TUN 路由（更改 IP 并绕过所有网络封锁）。
- **原生 Decky Loader 界面**：简洁清爽，完美契合 Steam Deck 快捷菜单风格。
- **开机自启与状态保存**：重启设备或在游戏/桌面模式间切换后，自动恢复服务状态。
- **极速低耗**：通过 `nfqws` 与 `nftables` 在内核层运行，几乎零 CPU 与电池消耗。

## 📥 安装说明

1. 从 [Releases](https://github.com/rosakodu/zapret-deck/releases) 页面下载最新版本（`zapret-deck.zip`）或手动构建。
2. 将 ZIP 文件复制到您的 Steam Deck。
3. 在 Steam 设置中启用 **开发者模式**，然后在 Decky Loader 设置中启用 **Developer mode** 并选择“从文件安装插件”。

## 🚀 使用方法

1. 按下 Steam Deck 上的 **`...`（快捷菜单）** 按钮并打开 **Decky Loader** 标签页。
2. 选择 **Zapret Deck**。
3. 点击 **“自动检测策略”**：
   - 插件将测试连接并自动选择可用的策略（如 `ALT`）。
   - **Zapret** 开关将被激活。
4. 如果需要完整 VPN，开启 **WARP** 开关 — 插件将自动注册并通过 Cloudflare WARP 路由您的流量。

## ⚖️ 开源协议

BSD-3-Clause License.
