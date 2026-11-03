# Analog Ön Kat (AFE) Değişiklikleri

Son güncelleme: 03.11.2026. Devre breadboard üzerindedir.

## Güncel devre (her kanal aynı)

```
                     Rf 8 MΩ
                 ┌───/\/\/\───┐
                 │  Cf 470 pF │
                 ├─────||─────┤
                 │            │
Piezo sıcak uç ──┤ −          │
                 │   TL074CN  ├── 22 kΩ ──┬── ADC (PA3 / PA1 / PA2)
Bias 1,47 V ─────┤ +                      │
                                       2×1 nF
Piezo soğuk uç ── analog GND              │
                                         GND

2,936 V (Discovery 3V) ── 10 kΩ ──┬── 10 kΩ ── GND
                                  ├── Bias 1,47 V
                                  └── 100 nF ∥ 100 µF ── GND
```

- **Kazanç:** orta bantta ≈ Cp/Cf ≈ 40. Ölçülen Cp ≈ 18,8 nF (blendajlı kablo dahil), Cf = 470 pF.
- **Alt köşe frekansı:** f = 1/(2π·Rf·Cf) = 42 Hz. Rf kazancı değiştirmez, yalnız bu köşeyi belirler.
- **Üst köşe frekansı:** 22 kΩ ve 2 nF ile yaklaşık 3,6 kHz (örtüşme önleme).
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
| X ve Z piezosu kablosu | Blendajsız teller, timsah | Aynı blendajlı kablo, timsahlar kısaltıldı | 50 Hz girişimi | 03.11'e kadar (kayıt alınmadı) |

**Cf denemeleri:** 1 nF'ta çıkış ~0,1 V ile küçük kaldı, 220 pF'a inildi, sweep'te kırpılmaması için 470 pF'ta karar kılındı. 18.10 kayıtlarının 220 pF ile mi 470 pF ile mi alındığı bilinmiyor.

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

Sayılar ve grafikler için [README.md](README.md#ölçüm-sonuçları).

| Sonuç | Değerlendirme |
|---|---|
| SD yavaş darbesi X ve Z'de yaklaşık 10 kat azaldı | Ölçüldü. Değişiklikler aynı anda yapıldığı için tek bir elemana bağlanamaz. |
| Y kanalında darbe aynı oranda düşmedi | 21.10'da 64–88 LSB kaldı. Y'ye özgü kuplaj yolu şüphesi var, doğrulanmadı. |
| Klavye zincirinde darbe arttı (21.10: 2–15, 01.11: 52–68 LSB) | Nedeni bilinmiyor. |
| Y'de 47–53 Hz bandı 13–23'ten 6–8 LSB'ye indi | Ölçüldü. Y'nin piezosu da değiştiği için tamamı blendaja bağlanamaz. |
| Y'de 1–45 Hz gürültü 22–34 LSB'ye çıktı | Blendajlı kablodan sonra görüldü. Kablo hareketi veya montaj şüphesi var. |
| Tek örnekli çatırtı sürüyor | X'te yaklaşık yarıya indi, Y ve Z'de değişmedi. Blendaj etkilemedi. |
| ADC pinleri sağlam | X/Z kabloları çaprazlanınca sinyal ve darbe kablo zincirini izledi. |

## Planlanan: MCP6004'e geçiş (yapılmadı)

Malzeme alındı (MCP6004-I/SL, SOIC-14 ve DIP adaptörü), lehim henüz yapılmadı.

- 9 V pil tamamen çıkarılacak, çünkü MCP6004'ün en yüksek beslemesi 6 V. 4. bacak Discovery 3V'a bağlanacak.
- Adaptör 16 bacaklı: çipin 1–7 bacakları ped 1–7'ye, 8–14 bacakları ped 10–16'ya gelecek, ped 8 ve 9 boş kalacak.
- Beklenen DC değerleri: 4–11 ≈ 2,93 V; çıkışlar bias ±10 mV.
- Eviren girişler (2, 6, 9, 13) multimetreyle ölçülmemeli, çünkü 10 MΩ'luk giriş direnci devreyi yükler.
