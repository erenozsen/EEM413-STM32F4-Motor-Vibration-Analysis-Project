# 26.11.2026: kazanç düşürüldü (Cf 2 nF), hoparlör testi

25.11 motor kayıtlarında sinyal ADC sınırlarına dayanıyordu (yüklü motorda Y ve Z örneklerinin ~%5'i 0 ya da 4095). Bu yüzden AFE kazancı düşürüldü ve firmware değiştirildi. Bu klasör, değişiklikten sonraki hoparlör testleridir: önce ses tam açık, sonra ses adım adım kısılarak.

## Yapılan değişiklikler

**AFE (üç kanalda aynı):**

| | Önce | Sonra |
|---|---|---|
| Geri besleme kapasitörü Cf | 470 pF | 2 × 1 nF film paralel = **2 nF** |
| Kazanç | ≈ Cp/470 pF | ×0,235 (**−12,6 dB**) |
| Alt köşe (Rf 8 MΩ aynı) | ~42 Hz | **~10 Hz** (motorun 49,5 Hz dönüş frekansı artık zayıflamıyor) |
| Anti-alias filtresi (22 kΩ + C) | 2 × 1 nF film = 2 nF, ~3,6 kHz | 1 nF film + 2,2 nF seramik (ölçülen ~1,5–1,7 nF) = ~2,6 nF, **~2,8 kHz** |

Filtreden çıkan 1 nF filmler Cf'de kullanıldı. Seramik kapasitörün değeri sıcaklıkla kaydığı için Cf'ye değil, yalnız kesim frekansını belirleyen filtreye kondu.

Hesaplanan toplam değişim (devre değerlerinden; motor kaydında doğrulanacak):

| Frekans | Değişim |
|---|---|
| 25 Hz | −7,4 dB |
| 49,5 Hz (motor 1×) | −10,4 dB |
| 100 Hz – 1 kHz | −12,6 dB |
| 3 kHz | −13,7 dB |
| 4,8 kHz | −14,2 dB |

**Firmware.** Projenin tamamı `Piezo_KaraKutu_2026-11-26.zip` içinde (CubeIDE projesi, Debug hariç). 16.11 sürümünden tek fark `main.c`; GitHub'da zip açmadan okunabilsin diye ayrıca `firmware/main.c` olarak da konuldu.
- Açılışta kayıt kendiliğinden başlamaz. Turuncu LED = hazır; mavi butonla başlar, tekrar basınca durur. Motor çalışırken kart resetlendiğinde kendi kendine yeni dosya açması böylece engellendi.
- Karta `OLAYLAR.TXT` günlüğü yazılır: her açılışta reset sebebi (güç açıldı / besleme düştü / reset pini), kaydın başladığı ve durduğu an, blok kaybı olup olmadığı, hata sebebi ve hangi SD işleminin hangi FatFs koduyla bozulduğu (ör. `f_sync FR=1`).
- **Kırmızı LED hata türünü gösterir:** hata kodu kadar kısa yanıp söner, 1,5 s bekler, tekrarlar.

  | Yanıp sönme | Anlamı |
  |---|---|
  | 1 | SD kart bağlanamadı |
  | 2 | SD'ye yazılamadı ya da kart dolu |
  | 3 | ADC/DMA hatası |
  | 4 | ADC durdu (örnek gelmiyor) |
  | 5 | Dosya açılamadı / kapatılamadı |
  | Yeşil yanarken sabit kırmızı | Kayıt sürüyor ama veri kaybı oldu |

- SD hatası olursa kart SD'yi yeniden bağlayıp günlüğe yazmayı dener; açılışta SD üç kez denenir. Hatadan sonra butona basılırsa SD yeniden bağlanıp yeni kayıt başlar.

## Düzenek

Üç piezo da çift taraflı bantla hoparlörün yan paneline, yan yana takılı. Fotoğrafta (`fotograflar/duzenek_3bant_yanyana.jpg`) **X en üstte, Y ortada, Z en altta**. Her kayıtta 100–5000 Hz sweep (gidiş-dönüş), öncesinde ve sonrasında ~5–10 s sessizlik. TL074, 9 V pil, SPI kapısı açık. İlk kayıtlar laptop USB'siyle, `seskisik5` ve `seskisik6` powerbank'le beslendi.

## Kayıtlar (`kayitlar/`)

Biçim: `uint16` X,Y,Z,X,Y,Z… (10 kHz). Her kanal için WAV (`_X/_Y/_Z.wav`, 10 kHz). Tüm WAV'larda **aynı kazanç** var: 1 LSB = 14,58 (18.11 akşamki sweep WAV'larıyla aynı), sesler doğrudan karşılaştırılabilir.

| Dosya | Ses | Kırpılma (0 / 4095'e dayanma) |
|---|---|---|
| `…_sesfull_sw100-5000_1_PIEZO001.BIN` | tam açık | üç kanal ~200–1500 Hz |
| `…_sesfull_sw100-5000_2_PIEZO002.BIN` | tam açık (tekrar) | üç kanal ~200–1500 Hz |
| `…_seskisik1_sw100-5000_PIEZO001.BIN` | 1. kısma | üç kanal ~100–1300 Hz |
| `…_seskisik2_sw100-5000_PIEZO002.BIN` | 2. kısma | Y 120–1200 Hz, Z 180–240 Hz |
| `…_seskisik3_sw100-5000_PIEZO003.BIN` | 3. kısma | yalnız Y 140–280 Hz |
| `…_seskisik4_sw100-5000_PIEZO004.BIN` | 4. kısma | yalnız Y 160–260 Hz |
| `…_seskisik5_sw100-5000_PIEZO003.BIN` | 5. kısma | yalnız Y ~200 Hz, çok kısa |
| `…_seskisik6_sw100-5000_kirpiksiz_PIEZO004.BIN` | 6. kısma | **yok** (Y tepe 1875 LSB @ 200 Hz) |

Günlükler: `OLAYLAR.TXT` (ses tam açık), `OLAYLAR_seskisik.TXT` (1–4), `OLAYLAR_powerbank.TXT` (5–6 ve aşağıdaki 2. kırmızı LED). Bütün düzgün kayıtlar butonla başlayıp durmuş, blok kaybı yok.

**`kayitlar/sorunlu/`:** iki kayıt kırmızı LED'le yarıda kesildi (`kirmiziLED1_laptop_…`, `kirmiziLED2_powerbank_…`), biri yanlış anda durduruldu. İki kırmızı LED olayı da reset butonuyla yapılan bir açılıştan sonraki ilk kayıtta oldu; günlükte hata satırı yok (SD o an yazılamıyordu). İkincisi powerbank'le ve sweep başlamadan, sessizlikte oldu; yani laptop USB'si ve ses seviyesi sebep değil. En güçlü şüphe: SD kart güç açıkken çıkarılıp takıldı ve ardından yalnız reset basıldı (SD'nin gücü kesilmedi). Bu yüzden firmware'e yukarıdaki hata kodları eklendi; artık SD'yi yalnız güç kapalıyken takıp çıkarıyoruz.

## Grafikler (`grafikler/`)

- `sw100-5000_Cf2nF_PIEZO002.png`: ses tam açık; üç kanal ~200–1500 Hz'te sınıra dayanıyor, 1,6 kHz üstü sığıyor.
- `ses_kisma_serisi.png`: her piezo için ses seviyesine göre tepe genlik. Ses kısıldıkça üst (X) ve alt (Z) piezo 3. adımdan itibaren sınırdan iniyor; orta piezo (Y) ~200 Hz'te en son, 6. adımda iniyor. Hoparlör panelinin bu frekanstaki titreşim modu ortada en büyük.
- `seskisik6_kirpilmasiz.png`: en kısık seste ham sinyal (üç piezo üst üste) ve frekansa göre tepe genlik. Hiçbir kanal kırpılmıyor; Y'nin alt tepesi sınıra yakın (~60 kod). Bu seste ~1,8 kHz üstü gürültüye yakın.

Sessiz bölümlerde gürültü 5–8 LSB, 50 Hz 1 LSB'nin altında; SD yazımından gelen çıtırtı yok.

## Sonuç ve açık soru

Ses tam açık hoparlör, 200–1500 Hz'te motordan muhtemelen çok daha güçlü titreşiyor. Kazancın ne kadar düştüğü hoparlörden ölçülemiyor (ses seviyesi önceki testlerden farklı); motorda aynı piezo yerleriyle alınacak yüksüz kayıtta 25.11 kayıtlarına oranla doğrulanacak (beklenen: 1× ~0,30 kat, harmonikler ~0,24 kat). Önerimiz bu kazançla motor ölçümüne geçmek; yüklü motorda kırpılma sürerse Cf 4,7 nF yapılabilir (−20 dB, alt köşe ~4 Hz), ancak o zaman en zayıf kanalda motorun 1× tepesi ~3 LSB'ye iner.

## Analiz betikleri (`analiz/`)

- `sw5000.py <BIN>`: özet (min/max, kırpılma, 0,5 s pencerelerde frekans ve tepe genlik)
- `sw5000_grafik.py <BIN> <png>`: ses tam açık grafiği
- `ses_kisma_grafik.py [kayıt klasörü] [çıktı klasörü]`: iki yeni grafik (argümansız çalıştırılırsa bu klasörün `kayitlar/` ve `grafikler/` klasörlerini kullanır)
