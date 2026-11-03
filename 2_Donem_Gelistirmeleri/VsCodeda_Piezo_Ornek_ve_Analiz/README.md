# Kayıtlar ve Okuma Betikleri

Kaydedicinin SD karta yazdığı ham kayıtlar, onlardan üretilen WAV dosyaları ve Python betikleri. Her kayıt klasöründe o gün ne yapıldığını anlatan bir README var.

## Kayıtlar

| Tarih | Klasör | Devrenin durumu | Sonuç |
|---|---|---|---|
| 18.10.2026 | [18.10.26](18.10.26/) | Eski devre | SD yazmalarının yarattığı bozulma ölçüldü, veri kaybı olmadığı doğrulandı |
| 21.10.2026 | [21 10 26 kapasitör ve topraklama](<21 10 26 kapasitör ve topraklama/>) | Yeni kapasitörler, ayrı SD GND, 2 nF | SD darbesi X ve Z'de yaklaşık 10 kat azaldı |
| 01.11.2026 | [01 11 26 blendajlı piezo Y ekseni](<01 11 26 blendajlı piezo Y ekseni/>) | Y kanalında blendajlı kablo | 50 Hz bandı Y'de düştü, 1–45 Hz gürültü arttı |

## Veri biçimi

Little-endian `uint16`, sıralama `X,Y,Z,X,Y,Z…`, kanal başına 10 kHz. Kanallar: X = PA3, Y = PA1, Z = PA2.

```python
import numpy as np
x, y, z = np.fromfile("21 10 26 kapasitör ve topraklama/PIEZOsarıX.BIN", dtype=np.uint16).reshape(-1, 3).T
volt = x * 2.936 / 4095
```

Her blok 4096 çerçeve, yani 409,6 ms. İlk blok dışında her bloğun ilk ~40 ms'i önceki yarının SD yazması sırasında alındığı için bozuktur. Analizlerde bu bölümü ayrı değerlendirin.

## Betikler

| Dosya | Ne yapar |
|---|---|
| `_ucluoku.py`, `_ucluoku2.py` | Üç kanalı çizer |
| `sesdonusturme.py` | Her kanal için WAV üretir |
| `_tekoku.py` | Eski tek kanallı kayıtları çizer |
| `_teksensorsesdonusturme.py`, `_teksensorsesdonustur2.py` | Eski tek kanallı kayıtlardan WAV üretir |

Betikleri kullanırken:

- Dosya adları kodun içinde sabit. Betiğin başındaki adı, kaydın klasörüyle birlikte yazın.
- Çizim betikleri ham ADC değerini gösterir. Gerilim için yukarıdaki formülü kullanın. Referans 3,3 V değil, kartta ölçülen 2,936 V.
- `sesdonusturme.py` her WAV'ı kendi tepesine göre normalize ediyor. SD spike'ları sesi baskılayabilir ve dosyaların ses yüksekliği karşılaştırılamaz.
