# 01.11.2026 Kayıtları: Y Kanalında Blendajlı Piezo

## Amaç

21.10 kayıtlarında Y kanalındaki 50 Hz girişimi X ve Z'ye göre yüksekti (47–53 Hz bandında 13–23 LSB). Blendajlı kablonun bunu azaltıp azaltmadığını görmek için yalnız Y kanalına blendajlı kablolu yeni bir piezo takıldı. X ve Z karşılaştırma için değiştirilmedi.

## Düzenek

**Devre:** TL074CN, 9 V pil, Rf 8 MΩ, Cf 470 pF, bias 1,47 V. Ayrıntılar: [AFE_DEGISIKLIKLERI.md](../../AFE_DEGISIKLIKLERI.md).

| Kanal | ADC pini | Piezo | Yeri | Kablo |
|---|---|---|---|---|
| X | PA3 | "Sarı" piezo | Hoparlör | Blendajsız, timsah |
| Y | PA1 | Yeni piezo | Hoparlör | **Blendajlı** (damar → seramik, blendaj → pirinç) |
| Z | PA2 | Klavyedeki piezo | Klavye | Blendajsız, timsah |

Blendajlı kabloyla ölçülen kapasitans 18,8–18,9 nF. Buna göre kazanç Cp/Cf ≈ 40. Lehimden sonra kısa devre yoktu.

**Kayıt akışı:** sessizlik → hoparlörden sweep → sessizlik.

## Yapılan denemeler

Bazı kayıtlarda kablolar bilerek değiştirildi. Amaç, darbe ve sinyalin ADC pinine mi yoksa kablo zincirine mi bağlı olduğunu görmekti.

| Dosya | Süre | Ses bölümü | Sweep'te sinyal std, X / Y / Z (LSB) | X/Z dizilimi | Not |
|---|---|---|---|---|---|
| `PIEZO001.BIN` | 22,2 s | 7,8–14,3 s | 495 / 740 / 35 | Normal | Temel kayıt |
| `PIEZO002.BIN` | 16,5 s | 5,3–9,8 s | 490 / 634 / 35 | Normal | 001 ile aynı düzen |
| `PIEZO003.BIN` | 15,6 s | 6,1–11,1 s | 37 / 613 / 461 | Çapraz | Hoparlör sinyali X'ten Z'ye geçti |
| `PIEZO004.BIN` | 22,2 s | 9,8–14,7 s | 146 / 1502 / 530 | Çapraz | X ve Y piezolarının hoparlördeki yeri değişti. **Y kırpıldı.** |
| `PIEZO005.BIN` | 16,5 s | 7,4–12,3 s | 440 / 1456 / 174 | Normal | X ve Y piezolarının yeri değişik. **Y kırpıldı.** Hoparlör sinyali tekrar Z'den X'e geçti |


## Sonuçlar

Sessiz bloklarda, 1 LSB ≈ 0,717 mV.

| Dosya | SD darbesi p-p, X / Y / Z | Çatırtı, X / Y / Z | 47–53 Hz, X / Y / Z | 1–45 Hz, X / Y / Z |
|---|---|---|---|---|
| 001 | 8 / 26 / 62 | 19 / 15 / 16 | 9,9 / 7,4 / 10,8 | 1,1 / 22,1 / 0,9 |
| 002 | 10 / 38 / 62 | 20 / 16 / 16 | 10,1 / 7,8 / 10,9 | 1,1 / 30,8 / 0,5 |
| 003 | 52 / 50 / 16 | 17 / 16 / 19 | 10,8 / 8,0 / 10,0 | 0,7 / 33,8 / 0,7 |
| 004 | 57 / 22 / 11 | 17 / 14 / 16 | 11,8 / 6,5 / 12,0 | 1,0 / 24,1 / 4,9 |
| 005 | 12 / 18 / 68 | 19 / 17 / 17 | 12,0 / 6,4 / 11,7 | 4,5 / 30,3 / 1,5 |

### Ne öğrendik

- **50 Hz bandı Y'de düştü.** 21.10'daki 13–23 LSB'den 6–8 LSB'ye indi, X ve Z 10–12 LSB'de kaldı. Y'nin piezosu da değiştiği için farkın tamamı blendaja bağlanamaz.
- **Y'de yeni bir sorun çıktı.** 1–45 Hz gürültü 22–34 LSB oldu, daha önce 0,7–2,6 LSB idi. X ve Z çoğunlukla 1 LSB civarında kaldı. Belirli bir frekansı yok ve düğmeye basıştan sonraki ilk saniyelerde daha yüksek. Bu yüzden kablo hareketi veya piezo montajı şüpheleniliyor, ama doğrulanmadı.
- **ADC pinleri sağlam.** X/Z çapraz bağlanınca sinyal ve SD darbesi pini değil kablo zincirini izledi (001–003).
- **SD darbesi zincire bağlı.** Hoparlördeki zincirde 8–16, klavyedeki zincirde 52–68 LSB. 21.10'da klavye zinciri 2–15 LSB idi. Artışın nedeni bilinmiyor.
- **Çatırtı değişmedi.** Üç kanalda 14–20 LSB, blendajlı Y dahil. Yani blendaj bu sorunu çözmedi.
- **Y'deki kırpılma gerçek aşırı genlikten.** 4 ve 5'te üstte ADC 4095'e (ses bölümünün yaklaşık %10–12'si), altta 0'a ulaştı. Ani sıçrama olmadığı için faz terslenmesi görülmedi. Diğer kanallarda belirgin harmonik bozulma da yok. Çözüm ses seviyesini düşürmek.
- **21.10'daki Z donması görülmedi.** Bu beş kayıtta donmuş bölüm yok.

## Sonrasında ne yapıldı

X ve Z piezolarına da aynı blendajlı kablo lehimlendi. Sıradaki kayıt üç blendajlı piezoyla, normal dizilimle (X = PA3, Y = PA1, Z = PA2) ve daha düşük sesle alınacak. Asıl bakılacak değer sessiz bölümdeki 1–45 Hz gürültü: X ve Z'de de artarsa kablo kaynaklı olması güçlenir.

## Dosyalar

- **`PIEZOnnn.BIN`:** Ham kayıt. Little-endian `uint16`, sıralama `X,Y,Z,…`, kanal başına 10 kHz. Gerilim: `V = kod · 2,936 / 4095`.
- **`Titreşim_Sesi_{X,Y,Z}_EkseniNNN.wav`:** Aynı numaralı kaydın kanalları, `sesdonusturme.py` ile üretildi. Her dosya kendi tepesine göre normalize edildiği için dosyaların ses yüksekliği birbiriyle karşılaştırılamaz. Dosya adındaki eksen ADC kanalını gösterir, çapraz kayıtlarda o piezonun kendisi değildir.
