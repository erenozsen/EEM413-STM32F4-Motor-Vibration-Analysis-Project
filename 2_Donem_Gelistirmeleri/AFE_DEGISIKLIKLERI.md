# Analog Ön Kat (AFE) Değişiklikleri

Son güncelleme: 26.11.2026. Devre breadboard üzerindedir.

## Güncel devre (her kanal aynı)

```
                     Rf 8 MΩ
                 ┌───/\/\/\───┐
                 │  Cf 2 nF   │   (2 × 1 nF film paralel)
                 ├─────||─────┤
                 │            │
Piezo sıcak uç ──┤ −          │
                 │   TL074CN  ├── 22 kΩ ──┬── ADC (PA3 / PA1 / PA2)
Bias 1,47 V ─────┤ +                      │
                                1 nF film ∥ 2,2 nF seramik
Piezo soğuk uç ── analog GND              │
                                         GND

2,936 V (Discovery 3V) ── 10 kΩ ──┬── 10 kΩ ── GND
                                  ├── Bias 1,47 V
                                  └── 100 nF ∥ 100 µF ── GND
```

- **Kazanç:** orta bantta ≈ Cp/Cf ≈ 9,4. Ölçülen Cp ≈ 18,8 nF (blendajlı kablo dahil), Cf = 2 nF. 470 pF'a göre ×0,235 (−12,6 dB).
- **Alt köşe frekansı:** f = 1/(2π·Rf·Cf) ≈ 10 Hz (470 pF'ta 42 Hz idi). Rf kazancı değiştirmez, yalnız bu köşeyi belirler.
- **Üst köşe frekansı:** 22 kΩ ve ~2,6 nF ile yaklaşık 2,8 kHz (örtüşme önleme; 2 nF film ile 3,6 kHz idi). 2,2 nF seramiğin ölçülen değeri ~1,5–1,7 nF ve sıcaklıkla kayıyor; bu yüzden yalnız filtrede, Cf'de değil.
- **Planlanan (01.12.2026):** Cf ~3 nF (üçüncü bir 1 nF film ya da tek 3,3 nF film). 470 pF'a göre −16 dB, alt köşe ~6,6 Hz.
- **Op-amp beslemesi:** 9 V pil, ölçülen 9,49 V. 4. bacak pil +, 11. bacak GND.

## Değişiklikler

| Nokta | Önce | Sonra | Neden | Tarih |
|---|---|---|---|---|
| Bias filtresi | 100 nF | 100 nF + 100 µF | SD akımının bias üzerinden sinyale geçmesini azaltmak | 20.10 |
| Op-amp besleme dekuplajı | Yok | 100 nF + 10 µF (4–11 arası) | Besleme gürültüsü | 20.10 |
| SD modülü besleme filtresi | 100 nF + 10 µF | 100 nF + 100 µF | SD yazma akım darbeleri | 20.10 |
| SD modülü GND dönüşü | Ortak | Discovery'nin başka bir GND pinine ayrı kablo | SD akımını analog topraktan ayırmak | 20.10 |
| ADC girişi | 22 kΩ | 22 kΩ + 2×1 nF film | Örtüşme önleme filtresi | 20.10 |
| Kullanılmayan 4. op-amp kanalı | Boşta | Bias'a bağlı izleyici | Boş kanalın salınmasını önlemek | 20.10 |
| Y piezosu kablosu | Blendajsız teller, timsah | Blendajlı kablo (damar → seramik, blendaj → pirinç) | 50 Hz girişimi | 01.11 |
| X ve Z piezosu kablosu | Blendajsız teller, timsah | Aynı blendajlı kablo, timsahlar kısaltıldı | 50 Hz girişimi | 03.11 (ilk kayıt 16.11) |
| Breadboard'daki giriş telleri | 15–20 cm açık tel | 2–3 cm; üç blendaj tek GND noktasında | Blendajsız kalan sıcak ucu kısaltmak | 16.11 |
| Geri besleme kapasitörü Cf | 470 pF | 2 × 1 nF film = 2 nF | Motorda sinyal ADC sınırlarına dayanıyordu (25.11); kazanç −12,6 dB | 26.11 |
| Anti-alias filtre kapasitörü | 2 × 1 nF film | 1 nF film + 2,2 nF seramik | Filtreden çıkan filmler Cf'de kullanıldı; kesim ~3,6 → ~2,8 kHz | 26.11 |

**Cf denemeleri:** 1 nF'ta çıkış ~0,1 V ile küçük kaldı, 220 pF'a inildi, hoparlör sweep'inde kırpılmaması için 470 pF'ta karar kılındı. 18.10 kayıtlarının 220 pF ile mi 470 pF ile mi alındığı bilinmiyor. Motor titreşimi hoparlörden çok büyük çıkınca (25.11, yüklü motorda Y ve Z örneklerinin ~%5'i kırpık) 2 nF'a geçildi (26.11): sağlam ve arızalı motor kırpılmadan kaydedildi. Danışmanın isteğiyle ~3 nF'a geçilecek.

## Bilerek yapılmayanlar

- **Schottky kırpıcı takılmadı.** 22 kΩ, ADC giriş koruma akımını en kötü durumda yaklaşık 0,22 mA ile sınırlıyor. Schottky sızıntısı ise ölçümü bozabilir.
- **Piezo soğuk ucu GND'de bırakıldı.** Bias'a taşınması da düşünüldü, ancak 100 µF eklenince gerekmedi. Motor gövdesine montajda GND daha güvenli.

## DC ölçümü (20.10, TL074)

| Nokta | Ölçülen |
|---|---|
| Besleme (4–11) | 9,49 V |
| Bias ve + girişler (3, 5, 10, 12) | 1,47 V |
| İzleyici çıkışı (14) | 1,47 V |
| Kanal çıkışları (1, 7, 8) | 1,35 V (bias'ın 120 mV altında) |

Bu fark, 8 MΩ üzerinden ~15 nA akıma karşılık gelir. Olası açıklama, TL074'ün tek beslemede giriş ortak mod sınırının altında çalışmasıdır. Bu **kanıtlanmış değil**: kırpılan kayıtlarda çıkış yaklaşık 11 mV'a kadar indi, yani çıkış salınımı beklenenden geniş. Kesin sınama MCP6004'e geçişle yapılacak.

## Ölçülen etki

Sayılar ve grafikler için [03.11 klasörünün README'si](<03 11 26 ilk paket ve önceki kayıtlar/README.md>) (18.10–16.11 ölçüm tablosu).

| Sonuç | Değerlendirme |
|---|---|
| SD yavaş darbesi X ve Z'de yaklaşık 10 kat azaldı | Ölçüldü. Değişiklikler aynı anda yapıldığı için tek bir elemana bağlanamaz. |
| Y kanalında darbe aynı oranda düşmedi | 21.10'da 64–88 LSB kaldı. Y'ye özgü kuplaj yolu şüphesi var, doğrulanmadı. |
| Klavye zincirinde darbe arttı (21.10: 2–15, 01.11: 52–68 LSB) | Nedeni bilinmiyor. |
| Y'de 47–53 Hz bandı 13–23'ten 6–8 LSB'ye indi | Ölçüldü. Y'nin piezosu da değiştiği için tamamı blendaja bağlanamaz. |
| Y'de 1–45 Hz gürültü 22–34 LSB'ye çıktı (01.11) | 16.11'de 0,7–0,8 LSB'ye indi. Arada kablo, giriş telleri ve piezo yeri değiştiği için neden belirlenemedi. |
| 16.11: üç kanal blendajlı, kısa giriş telleri | 47–53 Hz bandı X ~2, Y ~2,5, Z 1,3 LSB (01.11'de 6–12). SD darbesi kapı kapalıyken üç kanalda 7–12 LSB. |
| Tek örnekli çatırtı | Hiçbir AFE değişikliği çözmedi. Kaynağı SPI saat kenarlarıydı; firmware'deki SPI kapısıyla giderildi (16.11, [README](README.md)). |
| ADC pinleri sağlam | X/Z kabloları çaprazlanınca sinyal ve darbe kablo zincirini izledi. |
| Cf 2 nF (26.11) | Motorda kırpılma kalktı: sağlam motor tam yükte payın en fazla %45'i; arızalı motorda Z kayıt başına 2–86 örnek (≤ %0,1). Hoparlör ses tam açıkken 200–1500 Hz'te hâlâ kırpılıyor. Sessiz gürültü 5–8 LSB, 50 Hz < 1 LSB. |

## Planlanan: MCP6004'e geçiş (yapılmadı)

Malzeme alındı (MCP6004-I/SL, SOIC-14 ve DIP adaptörü), lehim henüz yapılmadı.

- 9 V pil tamamen çıkarılacak, çünkü MCP6004'ün en yüksek beslemesi 6 V. 4. bacak Discovery 3V'a bağlanacak.
- Adaptör 16 bacaklı: çipin 1–7 bacakları ped 1–7'ye, 8–14 bacakları ped 10–16'ya gelecek, ped 8 ve 9 boş kalacak.
- Beklenen DC değerleri: 4–11 ≈ 2,93 V; çıkışlar bias ±10 mV.
- Eviren girişler (2, 6, 9, 13) multimetreyle ölçülmemeli, çünkü 10 MΩ'luk giriş direnci devreyi yükler.
