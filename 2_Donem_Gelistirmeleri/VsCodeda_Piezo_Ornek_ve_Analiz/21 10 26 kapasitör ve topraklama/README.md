# 21.10.2026 Kayıtları: Yeni Kapasitörler ve Topraklama

## Ne yaptık

18.10 kayıtlarındaki SD yazma bozulmasını azaltmak için 20.10'da ön katı düzenledik, ertesi gün bu kayıtları aldık:

- Bias'a 100 µF eklendi.
- Op-amp beslemesine 100 nF + 10 µF eklendi.
- SD modülünün filtresi 100 nF + 100 µF oldu, GND dönüşü ayrı kabloya alındı.
- ADC girişlerine 2×1 nF eklendi.

Devre ayrıntıları: [AFE_DEGISIKLIKLERI.md](../../AFE_DEGISIKLIKLERI.md).

## Düzenek

- **X:** Hoparlörde. Her kayıtta farklı piezo, dosya adı o piezoyu gösterir.
- **Y:** Hoparlörde. Hangi piezonun takılı olduğu not edilmedi.
- **Z:** Klavyede.
- **Kayıt akışı:** ~9 s sessizlik, ~7 s hoparlörden sweep, ~10 s sessizlik.

## Kayıtlar

Değerler X / Y / Z sırasıyla LSB cinsindendir. Sinyal sütunu dışındakiler sessiz bloklardan hesaplandı.

| Dosya | Süre | Sweep | Sweep'te sinyal std | SD darbesi p-p | Çatırtı | 47–53 Hz |
|---|---|---|---|---|---|---|
| `PIEZOiyilehimX.BIN` | 26,4 s | 9,4–16,0 s | 424 / 790 / 15 | 14 / 88 / 11 | 21 / 24 / 19 | 10,3 / 13,5 / 5,9 |
| `PIEZOkötülehimX.BIN` | 26,6 s | 9,4–16,0 s | 571 / 354 / *dondu* | 24 / 84 / *geçersiz* | 20 / 20 / *geçersiz* | 6,6 / 19,5 / *geçersiz* |
| `PIEZOsarıX.BIN` | 25,5 s | 9,8–16,4 s | 388 / 473 / 20 | 18 / 64 / 15 | 18 / 19 / 22 | 10,7 / 22,7 / 8,0 |

## Sonuç

- **SD darbesi düştü.** X'te 154–248'den 14–24 LSB'ye, Z'de 217–540'tan 2–15 LSB'ye indi. Değişiklikler aynı anda yapıldığı için bu tek bir elemana bağlanamaz.
- **Y aynı oranda düşmedi.** 149–228'den 64–88 LSB'ye indi. Y'ye özgü bir kuplaj yolu olabilir, doğrulanmadı.
- **Çatırtı çözülmedi.** X'te 30–36'dan yaklaşık 20 LSB'ye indi, Y ve Z'de düşmedi.
- **Y'de 50 Hz yüksek kaldı.** Bir sonraki aşamada blendajlı kablo denemesinin nedeni bu oldu.
- **Orta nokta değişmedi.** Kanallar hâlâ ~1900 LSB (~1,36 V) civarında, hedef 2048 LSB. TL074 duruyor.

## Z kanalındaki donma

`PIEZOkötülehimX.BIN` kaydında Z, 3,0–12,4 s, 14,8–16,0 s ve 24,0–24,4 s arasında 3093 LSB'de (2,22 V) sabit kaldı, gürültüsü bile yoktu. Geçişlerde 2193 örnek 4095'e kırpıldı. Bu yüzden tablodaki Z değerleri bu kayıt için geçersiz.

Nedeni bilinmiyor. Dosya adındaki "kötü lehim" X'teki piezoyu anlatır, X kanalı bu kayıtta düzgün çalıştı. Donma diğer iki kayıtta ve 01.11 kayıtlarında görülmedi.

## Dosyalar

Yalnız ham `.BIN` kayıtları var, bu kayıtlardan WAV üretilmedi.
