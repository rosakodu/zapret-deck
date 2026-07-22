# 🚀 Zapret Deck

🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md) | 🇺🇦 [Українська](README.uk.md) | 🇹🇷 [Türkçe](README.tr.md) | 🇸🇦 [العربية](README.ar.md) | 🇮🇷 [فارسی](README.fa.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-TW.md)

---

<p align="center">
  <img src="assets/screenshot.png" alt="Zapret Deck Screenshot" width="650"/>
</p>

---

**Zapret Deck** — це потужний та зручний плагін для **Decky Loader**, призначений для обходу мережевих обмежень (Discord, YouTube тощо) та інтеграції **Cloudflare WARP VPN** безпосередньо в інтерфейс **Steam Deck** та пристроїв під управлінням **SteamOS / Bazzite / ChimeraOS**.

---

## ✨ Основні можливості

- ⚡ **Автопідбір стратегій у 1 клік**: розумний алгоритм тестує з'єднання та за секунди обирає найефективнішу стратегію обходу (`ALT`, `FAKE`, `SPLIT`).
- 🎯 **Зручне перемикання стратегій**: інтерактивний список із можливістю скасування вибору та ручного перемикання.
- 🛡 **Вбудований Cloudflare WARP VPN**: автоматична реєстрація акаунта WARP та повне тунелювання трафіку (зміна IP та обхід будь-яких блокувань).
- 🎨 **Нативний інтерфейс Decky Loader**: лаконічний дизайн, який ідеально інтегрується у меню Steam Deck.
- 🔄 **Автозапуск та збереження налаштувань**: служба автоматично відновлює роботу після перезавантаження або зміни режиму консолі.
- 🚀 **Висока швидкість та економія ресурсів**: обхід працює на рівні ядра через `nfqws` та `nftables`, майже не навантажуючи процесор та батарею.

---

## 🛠 Вимоги

- **Steam Deck** (LCD або OLED) / ПК з **SteamOS 3.x / Bazzite / ChimeraOS / Nobara**.
- Встановлений **[Decky Loader](https://decky.realm3.org/)**.

---

## 📦 Встановлення

### Вариант 1. Автоматично через Decky Loader (ZIP)

1. Відкрийте розділ **Releases** на GitHub та завантажте `zapret-deck.zip` з останнього релізу (`v1.0.0`).
2. Перейдіть у **Decky Loader** -> *Налаштування* -> *Розробник*.
3. Натисніть **Install Plugin from ZIP** та оберіть скачаний `zapret-deck.zip`.
4. Перезапустіть Decky Loader при необхідності.

### Варіант 2. Ручне встановлення через Термінал (SSH / Konsole)

Виконайте команду в консолі Steam Deck:

```bash
curl -sSL https://github.com/rosakodu/zapret-deck/releases/download/v1.0.0/zapret-deck.zip -o /tmp/zapret-deck.zip && \
sudo mkdir -p /home/deck/homebrew/plugins && \
sudo unzip -o /tmp/zapret-deck.zip -d /home/deck/homebrew/plugins/ && \
sudo chmod +x /home/deck/homebrew/plugins/zapret-deck/bin/* && \
sudo systemctl restart plugin_loader.service
```

---

## ⚖️ Ліцензія

Поширюється під ліцензією **BSD-3-Clause**.
