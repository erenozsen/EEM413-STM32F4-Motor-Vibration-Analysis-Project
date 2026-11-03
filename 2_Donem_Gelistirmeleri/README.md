# 2. Dönem Geliştirmeleri: Üç Eksenli Piezo Titreşim Kara Kutusu (STM32F407)

Asenkron motorlarda titreşim analizi ve arıza teşhisi için kaydedici. Üç piezo kanalı kanal başına 10 kHz ile örneklenir, ham ikili veri olarak SPI üzerinden microSD karta yazılır.

EEM 413 bitirme projesi, Eskişehir Teknik Üniversitesi. Hazırlayan: Eren Özşen. Danışman: Emin Germen.

**Durum (03.11.2026):** Kaydedici çalışıyor ve hoparlörle masa testleri sürüyor. Henüz motordan veri alınmadı, arıza teşhisi kısmı başlamadı.

## Klasör düzeni

| Yer | İçerik |
|---|---|
| [Piezo_KaraKutu_2026-11-03.zip](Piezo_KaraKutu_2026-11-03.zip) | Firmware projesi, belgeler ve analiz betiği |
| [VsCodeda_Piezo_Ornek_ve_Analiz/](VsCodeda_Piezo_Ornek_ve_Analiz/) | Kayıtlar, WAV dosyaları, okuma betikleri ve açıklamaları |
| [AFE_DEGISIKLIKLERI.md](AFE_DEGISIKLIKLERI.md) | Analog ön katta yapılan değişiklikler ve ölçümler |
| [grafikler/](grafikler/) | Kayıtlardan üretilen karşılaştırma grafikleri |
| [fotograflar/](fotograflar/) | Devre ve deney düzeneği fotoğrafları |

## Sistem

```
Piezo X/Y/Z → yük yükselteci → ADC1 (PA3, PA1, PA2) → DMA ping-pong tampon → SPI1 → microSD
                                  ↑
                         TIM3, 10 kHz tetik
```

- **Mikrodenetleyici:** STM32F407G-DISC1
- **Örnekleme:** TIM3 ile tetiklenen 3 kanallı ADC taraması, kanal başına 10 kHz, 144 çevrim örnekleme süresi
- **Tampon:** 2 × 4096 çerçeve (48 KB). Her yarı 409,6 ms'de dolar ve SD karta yazılır.
- **Dosya biçimi:** `PIEZOnnn.BIN`, little-endian `uint16`, sıralama `X,Y,Z,X,Y,Z…`
- **Gerilime çevirme:** `V = kod · 2,936 / 4095`. Kartta VDDA = VDD ≈ 2,936 V ölçüldü, 3,3 V değil.
- **Pinler:** X = PA3, Y = PA1, Z = PA2. SD: SCK PA5, MISO PA6, MOSI PA7, CS PA4. PA0 = kaydı durdur/başlat düğmesi.

## Bu dönemde neler değişti

### Firmware (Ekim 2026)

Ayrıntılar zip'teki `Docs/Uc_Piezolu_SD_Kaydedici_Incelemesi.pdf` dosyasında. Kaynak kodda en son değişiklik 18.10.2026 tarihlidir.

- Sessiz blok kaybına yol açan bayrak yarışı giderildi, kayıp bloklar `overrun_count` ile sayılıyor.
- Tampon 48 KB oldu, `f_sync` yaklaşık 0,8 s'de bir çalışıyor.
- Yazma hatası, kart dolması ve ADC durması algılanıyor.
- Mavi düğmeyle kayıt durdurulup başlatılabiliyor, her kayıt yeni bir `PIEZOnnn.BIN` dosyasına yazılıyor.
- SD kart 328 kHz'te başlatılıp 10,5 MHz'e geçiyor.
- X kanalı PA0'dan PA3'e taşındı.

### Donanım ve analiz (18.10 – 03.11.2026)

Devre ayrıntıları [AFE_DEGISIKLIKLERI.md](AFE_DEGISIKLIKLERI.md) dosyasında.

1. Kayıtlardaki "spike" seslerinin kaynağı SD yazmaları olarak belirlendi. Bozulma, yazmanın başladığı her bloğun ilk ~40 ms'inde görülüyor.
2. Veri kaybı olmadığı doğrulandı: 100 Hz tonun fazı blok sınırlarında sürekli kaldı. Sapma 0,08 rad'ın altındaydı, bir blok kaybolsaydı yaklaşık 0,25 rad atlama görülürdü.
3. Ön kat kapasitörleri ve topraklama düzenlendi. SD yazmasının yarattığı yavaş darbe X ve Z kanallarında yaklaşık 10 kat azaldı.
4. Y kanalına blendajlı kablo takıldı. 50 Hz bandı yaklaşık 2–3 kat düştü, ancak düşük frekans gürültüsü arttı. Ayrıntılar [01.11 kayıtlarının açıklamasında](<VsCodeda_Piezo_Ornek_ve_Analiz/01 11 26 blendajlı piezo Y ekseni/README.md>).
5. Blendajlı kablo X ve Z piezolarına da lehimlendi. Bu üç blendajlı düzenle henüz kayıt alınmadı.

## Ölçüm sonuçları

Sessiz bloklarda, kayıtlardan hesaplanmıştır. 1 LSB ≈ 0,717 mV.

| Metrik | Kanal | 18.10 | 21.10 | 01.11 |
|---|---|---|---|---|
| SD yavaş darbe, tepe-tepe (LSB) | X | 154–248 | 14–24 | zincire bağlı* |
| | Y | 149–228 | 64–88 | 18–50 |
| | Z | 217–540 | 2–15 | zincire bağlı* |
| Tek örnekli çatırtı, yazma penceresi ortalaması (LSB) | X | 30–36 | 18–21 | 17–20 |
| | Y | 13–19 | 19–24 | 14–17 |
| | Z | 12–15** | 13–22 | 16–19 |
| 47–53 Hz bant RMS (LSB) | Y | 12–19 | 13–23 | 6–8 |
| 1–45 Hz bant RMS (LSB) | Y | 0,7–2,6 | 0,7–2,0 | **22–34** |

\* 01.11'de X ve Z kabloları bazı kayıtlarda çaprazlandı. Darbe kanalı değil kablo zincirini izledi: hoparlördeki zincirde 8–16, klavyedeki zincirde 52–68 LSB.
\*\* 18.10 sweep kaydı hariç. O kayıtta Z kanalı anormaldi (119 LSB) ve kırpılma vardı.

![SD yazma darbesinin aşamalara göre değişimi](grafikler/darbe_tr.png)

![Bant RMS değerlerinin aşamalara göre değişimi](grafikler/bant_tr.png)

Bu değerler hoparlör ve klavye üzerindeki masa testlerinden alındı. Aynı aşamada birden fazla değişiklik yapıldığı için iyileşmeler tek bir nedene bağlanamaz.

## Açık sorunlar

- **Çatırtı çözülmedi.** X kanalında yaklaşık yarıya indi, Y ve Z'de değişmedi; üç kanalda da 14–20 LSB civarında sürüyor. Blendaj bunu çözmedi. Sıradaki aday, SPI baytlarını ADC örnekleme anının dışına kaydıran bir firmware denemesi. Bu deneme henüz yapılmadı.
- **Blendajlı Y kanalında 1–45 Hz gürültü arttı.** Kablo hareketi veya montaj kaynaklı olabilir. Neden henüz doğrulanmadı.
- **TL074 çalışma noktası.** Kanal çıkışları bias'ın ~120 mV altında (1,35 V). Giriş ortak mod sınırı bir hipotez olarak duruyor. Kesin sınama MCP6004'e geçiş olacak.
- **Bir kayıtta Z kanalı dondu.** `PIEZOkötülehimX.BIN` dosyasında Z bazı aralıklarda 3093 LSB'de kaldı. Sonraki kayıtlarda görülmedi, nedeni bilinmiyor.
- **Bilinen firmware hatası.** `fatfs_sd.c:320` satırında `TM_DELAY_Time2()` önünde `!` eksik. SDv1/MMC kartları (≤2 GB) etkiler, SDHC kartları etkilemez. Düzeltilmedi.
- **Dosya tarihleri sabit.** Kartta RTC kullanılmıyor. En yeni kaydı tarihinden değil numarasından anlayın.

## Sıradaki adımlar

1. Üç blendajlı piezoyla hoparlör testi
2. Motordan ön deneme (mıknatıslı montaj)
3. MCP6004'e geçiş ve DC kontrolü
4. Kalıcı montaj, sağlam ve arızalı motordan saha verisi
5. STFT/spektrogram ve arıza teşhisi

## Zip'teki projeyi kullanma

**Firmware:** STM32CubeIDE'de *File → Import → Existing Projects into Workspace* ile `Project_6_uc_Eksen_Piezo_wSPI_eg` klasörünü açıp derleyin. `Debug/` klasörü zip'te yok, CubeIDE derlerken yeniden oluşturur.

**Sayıları yeniden üretme:** Tablodaki değerler `analiz/analiz.py` ile üretildi. Kayıtlar zip'te değil, [VsCodeda_Piezo_Ornek_ve_Analiz/](VsCodeda_Piezo_Ornek_ve_Analiz/) klasöründe. Çalıştırmadan önce betikteki `KOK` yolunu bu klasöre göre değiştirin.

**Eski rapor:** Mayıs 2026 raporu (`Docs/`) eski tasarımı anlatır: TL084, 3,3 V ve PA0 gibi bilgiler güncel değildir.

## Üçüncü taraf kod

ST HAL/CMSIS ve USB Host kütüphaneleri, Tilen Majerle'nin `tm_stm32` kütüphaneleri ve FatFs kendi lisanslarıyla dosyaların içinde yer alır.
