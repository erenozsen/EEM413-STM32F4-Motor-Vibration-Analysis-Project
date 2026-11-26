# 26.11.2026: kazanç düşürüldü (Cf 2 nF), hoparlör testi

25.11 motor kayıtlarında sinyal ADC sınırlarına dayanıyordu (yüklü motorda Y ve Z örneklerinin ~%5'i 0 ya da 4095). Bu yüzden AFE kazancı düşürüldü ve firmware değiştirildi. Bu klasör, değişiklikten sonraki ilk hoparlör testidir.

## Yapılan değişiklikler

**AFE (üç kanalda aynı):**

| | Önce | Sonra |
|---|---|---|
| Geri besleme kapasitörü Cf | 470 pF | 2 × 1 nF film paralel = **2 nF** |
| Kazanç | ≈ Cp/470 pF | ×0,235 (**−12,6 dB**) |
| Alt köşe (Rf 8 MΩ aynı) | ~42 Hz | **~10 Hz** (motorun 49,5 Hz dönüş frekansı artık zayıflamıyor) |
| Anti-alias filtresi (22 kΩ + C) | 2 × 1 nF film = 2 nF, ~3,6 kHz | 1 nF film + 2,2 nF seramik (ölçülen ~1,5–1,7 nF) = ~2,6 nF, **~2,8 kHz** |

Filtreden çıkan 1 nF filmler Cf'de kullanıldı. Seramik kapasitörün değeri sıcaklıkla kaydığı için Cf'ye değil, yalnız kesim frekansını belirleyen filtreye kondu.

**Firmware.** Projenin tamamı `Piezo_KaraKutu_2026-11-26.zip` içinde (CubeIDE projesi, Debug hariç). 16.11 sürümünden tek fark `main.c`; GitHub'da zip açmadan okunabilsin diye ayrıca `firmware/main.c` olarak da konuldu. Değişiklikler:
- Açılışta kayıt kendiliğinden başlamaz. Turuncu LED = hazır; mavi butonla başlar, tekrar basınca durur. Motor çalışırken kart resetlendiğinde kendi kendine yeni dosya açması böylece engellendi.
- Karta `OLAYLAR.TXT` günlüğü yazılır: her açılışta reset sebebi (güç açıldı / besleme düştü / reset pini), kaydın başladığı ve durduğu an, blok kaybı olup olmadığı, hata sebebi.
- Hatadan sonra butona basılırsa kart yeniden bağlanıp yeni kayıt denenir.

## Düzenek

Üç piezo da çift taraflı bantla hoparlörün yan paneline, yan yana takılı. Fotoğrafta (`fotograflar/duzenek_3bant_yanyana.jpg`) **X en üstte, Y ortada, Z en altta**. Ses **tam açık**, 100–5000 Hz sweep (gidiş-dönüş, ~11 s); öncesinde ~10 s, sonrasında ~7–10 s sessizlik. TL074, 9 V pil, SPI kapısı açık.

## Kayıtlar (`kayitlar/`)

| Dosya | Süre |
|---|---|
| `hoparlor_3bant_yanyana_XYZ_sesfull_sw100-5000_1_PIEZO001.BIN` | 28,0 s |
| `hoparlor_3bant_yanyana_XYZ_sesfull_sw100-5000_2_PIEZO002.BIN` | 30,3 s (tekrar) |

- Biçim: `uint16` X,Y,Z,X,Y,Z… (10 kHz).
- Her kanal için WAV (`_X/_Y/_Z.wav`, 10 kHz). Tüm WAV'larda **aynı kazanç** var: 1 LSB = 14,58. Bu, 18.11 akşamki 100–2500 Hz sweep WAV'larıyla aynı kazanç; sesler doğrudan karşılaştırılabilir.
- `OLAYLAR.TXT`: tek açılış, iki kayıt butonla başlayıp durmuş, blok kaybı yok.

## Sonuç (`grafikler/sw100-5000_Cf2nF_PIEZO002.png`)

- **~200–1500 Hz:** ses tam açıkken üç kanal da hâlâ ADC sınırlarına (0 / 4095) dayanıyor.
- **1,6 kHz üstü:** sığıyor. Ortadaki piezo (Y) en fazla ~1550 LSB, X ve Z ~800 LSB tepe.
- **Sessiz bölüm:** gürültü 5–8 LSB, 50 Hz 1 LSB'nin altında. SD yazımından gelen çıtırtı yok.
- İki kayıt birbirinin aynısı.

Ses seviyesi önceki hoparlör testlerinden farklı (tam açık), bu yüzden kazancın ne kadar düştüğü bu kayıttan ölçülemiyor. Kazanç düşüşü, motorda aynı piezo yerleriyle alınacak yüksüz kayıtta, 25.11 kayıtlarına oranla doğrulanacak. Beklenen: 1× ~0,30 kat, harmonikler ~0,24 kat.

## Açık soru

Ses tam açık hoparlör, 200–1500 Hz'te motordan muhtemelen çok daha güçlü titreşiyor. Önerimiz bu kazançla motor ölçümüne geçmek. Yüklü motorda kırpılma sürerse Cf 4,7 nF yapılabilir (−20 dB, alt köşe ~4 Hz). Ancak o durumda en zayıf kanalda motorun 1× tepesi ~3 LSB'ye iner ve gürültüye yaklaşır.

## Analiz betikleri (`analiz/`)

- `sw5000.py <BIN>`: özet (min/max, kırpılma, 0,5 s pencerelerde frekans ve tepe genlik)
- `sw5000_grafik.py <BIN> <png>`: grafik
