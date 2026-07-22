# zapret-deck

[🇺🇸 English](README.md) | [🇷🇺 Русский](README.ru.md) | [🇺🇦 Українська](README.uk.md) | [🇨🇳 简体中文](README.zh-CN.md) | [🇹🇼 繁體中文](README.zh-TW.md) | [🇸🇦 العربية](README.ar.md) | [🇮🇷 فارسی](README.fa.md) | [🇹🇷 Türkçe](README.tr.md)

Steam Deck için `zapret` (`nfqws`) stratejilerini kullanarak DPI engellerini (YouTube, Discord vb.) aşmanızı ve otomatik sistem genelinde yönlendirme ile `usque` kullanarak **Cloudflare WARP VPN**'e bağlanmanızı sağlayan bir Decky Loader eklentisi.

![Screenshot](assets/screenshot.png)

## 📋 Özellikler

- **Tek Tıkla Otomatik Strateji Algılama**: Akıllı algoritma engellenen hedefleri test eder ve saniyeler içinde en etkili stratejiyi seçer (`ALT`, `FAKE`, `SPLIT`).
- **Kolay Strateji Değiştirme**: İptal etme ve manuel seçim seçeneğine sahip etkileşimli strateji listesi.
- **Entegre Cloudflare WARP VPN**: Otomatik WARP hesabı kaydı ve tam tünel yönlendirmesi (IP adresinizi değiştirir ve tüm ağ engellerini aşar).
- **Yerel Decky Loader Arayüzü**: Steam Deck Hızlı Erişim Menüsü stiliyle mükemmel uyum sağlayan temiz arayüz.
- **Otomatik Başlatma ve Kalıcılık**: Konsol yeniden başlatıldığında veya oyun/masaüstü modları arasında geçiş yapıldığında hizmet durumunu otomatik olarak geri yükler.
- **Yüksek Hız ve Düşük Kaynak Kullanımı**: `nfqws` ve `nftables` aracılığıyla çekirdek seviyesinde çalışır, işlemci veya pil ömrüne neredeyse sıfır yük bindirir.
