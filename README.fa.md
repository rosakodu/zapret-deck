# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

یک پلاگین مستقل Decky Loader برای Steam Deck که ترکیبی از دور زدن DPI از طریق **Zapret** (nfqws) و تونل VPN امن از طریق **Cloudflare WARP (پروتکل MASQUE)** را ارائه می‌دهد — برای دور زدن سانسور اینترنت و کُندسازی (از جمله YouTube و Discord) مستقیماً در حالت بازی، بدون هیچ برنامه خارجی.

> **توجه:** این پلاگین کاملاً مستقل است. نیازی به نصب Amnezia VPN، warp-cli یا هر مدیر رابط گرافیکی ندارد. تمام فایل‌های اجرایی درون پلاگین تعبیه شده‌اند.

![اسکرین‌شات](assets/screenshot.png)

## 📋 ویژگی‌ها

- **دو حالت دور زدن**: جابجایی بین **Zapret (دور زدن DPI)** برای دسترسی مستقیم بدون کُندسازی (بهترین برای YouTube 4K و Discord) و **WARP VPN (MASQUE)** برای تونل کامل.
- **پروتکل MASQUE**: WARP از طریق MASQUE (HTTP/3 روی QUIC) متصل می‌شود که از ترافیک HTTPS معمولی قابل تشخیص نیست.
- **تشخیص خودکار استراتژی**: Zapret به طور خودکار بهترین پارامترهای دور زدن DPI برای ISP شما را آزمایش و انتخاب می‌کند.
- **مدیر دامنه**: اضافه کردن و مدیریت دامنه‌ها مستقیماً از رابط پلاگین.
- **استقلال ۱۰۰٪**: در فضای کاربری اجرا می‌شود. نیازی به کامپایل ماژول هسته ندارد.

## 📥 نصب

1. آخرین نسخه (`zapret-deck.zip`) را از صفحه [Releases](https://github.com/rosakodu/zapret-deck/releases) دانلود کنید.
2. فایل ZIP را به Steam Deck خود منتقل کنید.
3. **حالت توسعه‌دهنده** را در تنظیمات سیستم Steam Deck فعال کنید.
4. در تنظیمات Decky Loader، حالت توسعه‌دهنده را فعال کرده و "نصب پلاگین از فایل" را انتخاب کنید.

## ⚖️ اعتبارات و منابع

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — کلاینت متن‌باز Cloudflare WARP MASQUE.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — موتور قدرتمند دور زدن DPI به نام `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — استراتژی‌های اصلی دور زدن DPI برای YouTube و Discord.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — پیکربندی shell لینوکس و منطق تنظیم خودکار.

## ⚖️ مجوز
BSD-3-Clause
