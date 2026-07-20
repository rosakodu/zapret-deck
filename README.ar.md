# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

مكوّن إضافي مستقل لـ Decky Loader على Steam Deck، يجمع بين تجاوز DPI عبر **Zapret** (nfqws) ونفق VPN آمن عبر **Cloudflare WARP (بروتوكول MASQUE)** — لتجاوز حجب الإنترنت وتقييده (بما في ذلك YouTube وDiscord) مباشرةً في وضع الألعاب، دون أي تطبيقات خارجية.

> **ملاحظة:** المكوّن الإضافي مستقل تمامًا. لا يتطلب تثبيت Amnezia VPN أو warp-cli أو أي مدير واجهة رسومية. جميع الملفات الثنائية مدمجة بداخله.

![لقطة شاشة](assets/screenshot.png)

## 📋 الميزات

- **وضعان للتجاوز**: التبديل بين **Zapret (تجاوز DPI)** للوصول المباشر دون إبطاء (الأفضل لـ YouTube 4K وDiscord) و**WARP VPN (MASQUE)** للنفق الكامل.
- **بروتوكول MASQUE**: يتصل WARP عبر MASQUE (HTTP/3 فوق QUIC)، مما يجعله غير قابل للتمييز عن حركة HTTPS العادية.
- **الكشف التلقائي عن الاستراتيجية**: يختبر Zapret تلقائيًا ويختار أفضل معاملات تجاوز DPI لمزود الإنترنت الخاص بك.
- **مدير النطاقات**: إضافة وإدارة النطاقات للتجاوز مباشرةً من واجهة المكوّن.
- **استقلالية 100%**: يعمل في فضاء المستخدم. لا يتطلب تجميع وحدة النواة.

## 📥 التثبيت

1. قم بتنزيل الإصدار الأخير (`zapret-deck.zip`) من صفحة [Releases](https://github.com/rosakodu/zapret-deck/releases).
2. انقل ملف ZIP إلى Steam Deck الخاص بك.
3. قم بتمكين **وضع المطور** في إعدادات نظام Steam Deck.
4. في إعدادات Decky Loader، قم بتمكين وضع المطور واختر "تثبيت مكوّن إضافي من ملف".

## ⚖️ الاعتمادات والمصادر

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — عميل Cloudflare WARP MASQUE مفتوح المصدر.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — محرك تجاوز DPI القوي `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — استراتيجيات تجاوز DPI الأصلية لـ YouTube وDiscord.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — تكوين الصدفة لـ Linux ومنطق الضبط التلقائي.

## ⚖️ الترخيص
BSD-3-Clause
