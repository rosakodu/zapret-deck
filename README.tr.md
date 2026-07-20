# Zapret-Deck

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

Steam Deck için bağımsız bir Decky Loader eklentisi; **Zapret** (nfqws) üzerinden DPI atlatma ve **Cloudflare WARP (MASQUE protokolü)** üzerinden güvenli VPN tünelini birleştirir — herhangi bir harici uygulama olmadan oyun modunda internet sansürünü ve hız kısıtlamalarını (YouTube ve Discord dahil) doğrudan atlar.

> **Not:** Bu eklenti tamamen bağımsızdır. Amnezia VPN, warp-cli veya herhangi bir masaüstü GUI yöneticisinin yüklenmesini gerektirmez. Tüm ikili dosyalar eklentinin içinde paketlenmiştir.

![Ekran Görüntüsü](assets/screenshot.png)

## 📋 Özellikler

- **İki Atlatma Modu**: **Zapret (DPI Atlatma)** (YouTube 4K / Discord için en iyisi) ile **WARP VPN (MASQUE)** tam tünel VPN arasında geçiş yapın.
- **MASQUE Protokolü**: WARP, normal HTTPS trafiğinden ayırt edilemeyen MASQUE (HTTP/3 over QUIC) üzerinden bağlanır.
- **Otomatik Strateji Tespiti**: Zapret, ISP'niz için en iyi DPI atlatma parametrelerini otomatik olarak test edip seçer.
- **Alan Adı Yöneticisi**: Doğrudan eklenti arayüzünden atlanacak alan adlarını ekleyin ve yönetin.
- **%100 Bağımsız**: Kullanıcı alanında çalışır. Çekirdek modülü derleme gerektirmez.

## 📥 Kurulum

1. [Releases](https://github.com/rosakodu/zapret-deck/releases) sayfasından son sürümü (`zapret-deck.zip`) indirin.
2. ZIP arşivini Steam Deck'inize aktarın.
3. Steam Deck Sistem Ayarları'nda **Geliştirici Modu**'nu etkinleştirin.
4. Decky Loader ayarlarında geliştirici modunu etkinleştirin ve "Dosyadan eklenti yükle"yi seçin.

## ⚖️ Katkıda Bulunanlar ve Kaynaklar

- **[Diniboy1123/usque](https://github.com/Diniboy1123/usque)** — Açık kaynaklı Cloudflare WARP MASQUE istemcisi.
- **[bol-van/zapret](https://github.com/bol-van/zapret)** — Güçlü DPI atlatma motoru `nfqws`.
- **[flowseal/zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube)** — YouTube ve Discord için orijinal DPI atlatma stratejileri.
- **[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)** — Linux shell yapılandırması ve otomatik ayarlama mantığı.

## ⚖️ Lisans
BSD-3-Clause
