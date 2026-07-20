# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

Автономний плагін Decky Loader для Steam Deck, що поєднує обхід DPI через **Zapret** (nfqws) та безпечний VPN-тунель через **Cloudflare WARP (протокол MASQUE)** — обхід інтернет-блокувань та уповільнень (включно з YouTube і Discord) прямо в ігровому режимі, без сторонніх застосунків.

> **Примітка:** Плагін повністю автономний. Не потребує Amnezia VPN, warp-cli або будь-яких GUI-менеджерів. Усі бінарні файли включені всередину плагіну.

![Скріншот](assets/screenshot.png)

## 📋 Можливості

- **Два режими обходу**: Перемикайтесь між **Zapret (Обхід DPI)** для прямого доступу без уповільнень (найкраще для YouTube 4K і Discord) та **WARP VPN (MASQUE)** для повного VPN-тунелю.
- **Протокол MASQUE**: WARP підключається через MASQUE (HTTP/3 поверх QUIC), що є неможливим для розрізнення від звичайного HTTPS-трафіку.
- **Авто-вибір стратегії**: Zapret автоматично тестує та вибирає найкращі параметри обходу DPI.
- **Менеджер заблокованих доменів**: Додавайте домени для обходу прямо з інтерфейсу плагіну.
- **100% автономність**: Без компіляції ядра, без вимкнення read-only файлової системи SteamOS.

## 📥 Встановлення

1. Завантажте останній реліз (`zapret-deck.zip`) зі сторінки [Releases](https://github.com/rosakodu/zapret-deck/releases).
2. Перенесіть ZIP-архів на ваш Steam Deck.
3. Увімкніть **Режим розробника** у системних налаштуваннях Steam Deck.
4. У налаштуваннях Decky Loader увімкніть режим розробника та виберіть «Встановити плагін з файлу».

## ⚖️ Авторство та джерела

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — open-source клієнт Cloudflare WARP через MASQUE.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — потужний рушій обходу DPI `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — оригінальні стратегії обходу DPI для YouTube і Discord.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — конфігурація для Linux.

## ⚖️ Ліцензія
BSD-3-Clause
