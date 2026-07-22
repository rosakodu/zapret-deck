# 🚀 Zapret Deck

🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md) | 🇺🇦 [Українська](README.uk.md) | 🇹🇷 [Türkçe](README.tr.md) | 🇸🇦 [العربية](README.ar.md) | 🇮🇷 [فارسی](README.fa.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-TW.md)

---

<p align="center">
  <img src="assets/screenshot.png" alt="Zapret Deck Screenshot" width="650"/>
</p>

---

**Zapret Deck**, **Steam Deck** ve **SteamOS / Bazzite / ChimeraOS** çalıştıran cihazlarda ağ kısıtlamalarını (Discord, YouTube vb.) aşmak ve **Cloudflare WARP VPN** entegrasyonu sağlamak için tasarlanmış güçlü ve kullanımı kolay bir **Decky Loader** eklentisidir.

---

## ✨ Özellikler

- ⚡ **Tek Tıkla Otomatik Strateji Algılama**: Akıllı algoritma engellenen hedefleri test eder ve saniyeler içinde en etkili stratejiyi seçer (`ALT`, `FAKE`, `SPLIT`).
- 🎯 **Kolay Strateji Değiştirme**: İptal etme ve manuel seçim seçeneğine sahip etkileşimli strateji listesi.
- 🛡 **Entegre Cloudflare WARP VPN**: Otomatik WARP hesabı kaydı ve tam tünel yönlendirmesi (IP adresinizi değiştirir ve tüm ağ engellerini aşar).
- 🎨 **Yerel Decky Loader Arayüzü**: Steam Deck Hızlı Erişim Menüsü stiliyle mükemmel uyum sağlayan temiz arayüz.
- 🔄 **Otomatik Başlatma ve Kalıcılık**: Konsol yeniden başlatıldığında veya oyun/masaüstü modları arasında geçiş yapıldığında hizmet durumunu otomatik olarak geri yükler.
- 🚀 **Yüksek Hız ve Düşük Kaynak Kullanımı**: `nfqws` ve `nftables` aracılığıyla çekirdek seviyesinde çalışır, işlemci veya pil ömrüne neredeyse sıfır yük bindirir.

---

## 🛠 Gereksinimler

- **Steam Deck** (LCD veya OLED) / **SteamOS 3.x / Bazzite / ChimeraOS / Nobara** çalıştıran bilgisayar.
- Yüklü **[Decky Loader](https://decky.realm3.org/)**.

---

## 📦 Kurulum

### Yöntem 1. Decky Loader üzerinden Otomatik (ZIP)

1. GitHub **Releases** bölümünden en son sürümün `zapret-deck.zip` dosyasını indirin.
2. **Decky Loader** -> *Ayarlar* -> *Geliştirici* menüsünü açın.
3. **Install Plugin from ZIP** seçeneğine tıklayın ve `zapret-deck.zip` dosyasını seçin.

### Yöntem 2. Terminal Üzerinden Manuel (SSH / Konsole)

Steam Deck terminalinizde şu komutu çalıştırın:

```bash
curl -sSL https://github.com/rosakodu/zapret-deck/releases/download/v1.0.0/zapret-deck.zip -o /tmp/zapret-deck.zip && \
sudo mkdir -p /home/deck/homebrew/plugins && \
sudo unzip -o /tmp/zapret-deck.zip -d /home/deck/homebrew/plugins/ && \
sudo chmod +x /home/deck/homebrew/plugins/zapret-deck/bin/* && \
sudo systemctl restart plugin_loader.service
```

---

## ⚖️ Lisans

**BSD-3-Clause** lisansı altında dağıtılmaktadır.
