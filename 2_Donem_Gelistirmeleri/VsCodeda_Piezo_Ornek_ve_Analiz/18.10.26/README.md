# 18.10.2026 Kayıtları: Yeni Firmware, Eski Devre

## Ne yaptık

Ekim firmware düzeltmelerinden sonra sistemin nasıl çalıştığını görmek için üç kayıt aldık. WAV dosyalarında duyulan "spike" seslerinin kaynağını bu kayıtların analiziyle bulduk. Ön kat henüz değiştirilmemişti: bias'ta yalnız 100 nF vardı, op-amp beslemesinde kapasitör ve ADC girişinde 2 nF yoktu, SD GND ortaktı.

Bu kayıtların 220 pF ile mi 470 pF ile mi alındığı bilinmiyor.

## Kayıtlar

Değerler X / Y / Z sırasıyla LSB cinsindendir ve sessiz bloklardan hesaplandı.

| Dosya | Süre | İçerik | SD darbesi p-p | Çatırtı | 47–53 Hz |
|---|---|---|---|---|---|
| `sonPIEZO3.BIN` | 15,5 s | Çoğunlukla sessiz, 6–11 s arasında X ve Y'de sinyal var | 248 / 228 / 220 | 33 / 13 / 12 | 12,6 / 15,6 / 3,9 |
| `Yenideneme 100hz_PIEZO001.BIN` | 25,4 s | 100 Hz ton, ~5–13 s | 242 / 182 / 217 | 36 / 19 / 15 | 10,1 / 18,7 / 7,1 |
| `yenisweepPIEZO3.BIN` | 19,0 s | Sweep, X ve Y'de ~4–13 s | 154 / 149 / *anormal* | 30 / 14 / *anormal* | 12,6 / 11,5 / *anormal* |

## Sonuç

- **Spike sesinin kaynağı SD yazması.** İlk blok dışında her bloğun başındaki ~40 ms bozuk. İlk blok temiz. Bu bozulmanın iki parçası var: birkaç ms'de tepe yapıp sönen yavaş bir darbe ve yoğun tek örnekli çatırtı.
- **Veri kaybı yok.** 100 Hz tonun fazı blok sınırlarında sürekli kaldı, sapma 0,08 rad'ın altındaydı. Bir blok kaybolsaydı yaklaşık 0,25 rad atlama görülürdü.
- **SD yazması zamanında bitiyor.** Süre genelde 37–44 ms, 409,6 ms'lik sınırın çok altında.
- **Orta nokta düşük.** Kanallar ~1900 LSB (~1,36 V) civarında, hedef 2048 LSB.
- **Sweep kaydında Z anormal.** Sessiz bölümde bile gürültülü, 7–8 s ve 14–18 s civarında patlamalar ve 0/4095 kırpılma var. Nedeni bulunamadı. Diğer iki kayıtta Z düzgün.

Bu bulgular üzerine 20.10'da ön kat düzenlendi. Sonuçlar için [21.10 kayıtları](<../21 10 26 kapasitör ve topraklama/README.md>).

## Dosyalar

- **`.BIN`:** Ham kayıtlar.
- **`.wav`:** Her kaydın üç kanalı, `sesdonusturme.py` ile üretildi. Her dosya kendi tepesine göre normalize edildiği için ses yükseklikleri birbiriyle karşılaştırılamaz.
