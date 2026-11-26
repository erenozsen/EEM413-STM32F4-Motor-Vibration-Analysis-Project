# 2. Dönem Geliştirmeleri: Üç Eksenli Piezo Titreşim Kara Kutusu (STM32F407)

Asenkron motorlarda titreşim analizi ve arıza teşhisi için kaydedici. Üç piezo kanalı kanal başına 10 kHz ile örneklenir, ham ikili veri olarak SPI üzerinden microSD karta yazılır.

EEM 413 bitirme projesi, Eskişehir Teknik Üniversitesi. Hazırlayan: Eren Özşen. Danışman: Emin Germen.

**Durum (26.11.2026):** Kaydedici çalışıyor; SD yazma çatırtısı SPI kapısıyla giderildi. Kazanç düşürüldü (Cf 470 pF → 2 nF) ve ilk motor verisi alındı: sağlam motor ve rulman arızalı motor, yüksüz / yarım yük / tam yükte, kırpılmadan kaydedildi. Arızalı motorda 9 bilyeli rulmanın iç bilezik arıza frekansı (5,40 × dönüş frekansı) üç yükte de görüldü. Sıradaki adım, Cf ~3 nF ile ölçümlerin tekrarı.

## Klasör düzeni

Her güncelleme kendi tarihli klasöründe; her klasörde o günü anlatan bir README var.

| Klasör | İçerik |
|---|---|
| [03 11 26 ilk paket ve önceki kayıtlar/](<03 11 26 ilk paket ve önceki kayıtlar/>) | İlk paket: Ekim firmware düzeltmeleri, 18.10 / 21.10 / 01.11 kayıtları, AFE düzenlemeleri, blendajlı kablo; 18.10–16.11 ölçüm tablosu |
| [16 11 26 SPI kapısı güncellemesi/](<16 11 26 SPI kapısı güncellemesi/>) | Danışmanın SPI kapısı: kapı açık/kapalı A/B testi, çatırtının giderilmesi |
| [18 11 26 montaj karşılaştırması/](<18 11 26 montaj karşılaştırması/>) | Hoparlörde eski stil, mıknatıslı ve çift taraflı bantlı montajın karşılaştırması, 100–2500 Hz frekans tepkisi |
| [26 11 26 Cf 2nF hoparlör testi/](<26 11 26 Cf 2nF hoparlör testi/>) | Kazanç düşürüldü (Cf 2 nF), butonla başlayan ve günlük tutan firmware, hoparlörde ses kısma serisi. **Güncel firmware zip'i burada.** |
| [26 11 26 Cf 2nF motor sağlam ve rulman arızalı/](<26 11 26 Cf 2nF motor sağlam ve rulman arızalı/>) | İlk motor veri seti: sağlam ve rulman arızalı motor, üç yük durumu, spektrum ve zarf analizi |
| [AFE_DEGISIKLIKLERI.md](AFE_DEGISIKLIKLERI.md) | Analog ön kattaki bütün değişiklikler ve güncel devre |

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
- **Pinler:** X = PA3, Y = PA1, Z = PA2. SD: SCK PA5, MISO PA6, MOSI PA7, CS PA4. PA0 = kaydı başlat/durdur düğmesi.
- **Kullanım (26.11 firmware):** açılışta turuncu LED = hazır; mavi düğme kaydı başlatır ve durdurur. Karttaki `OLAYLAR.TXT` her açılışın reset sebebini, kayıtların başlama/bitişini ve hataları yazar. Hata olunca kırmızı LED hata kodu kadar yanıp söner.

## Zaman çizelgesi

| Tarih | Ne yapıldı | Sonuç |
|---|---|---|
| Ekim | Firmware düzeltmeleri (blok kaybı, tampon, hata algılama) | Veri kaybı yok |
| 18.10 – 03.11 | AFE kapasitörleri, topraklama, blendajlı kablo | SD darbesi X ve Z'de ~10 kat azaldı |
| 16.11 | SPI kapısı | SD yazma çatırtısı tamamen kayboldu |
| 18.11 | Montaj karşılaştırması | Mıknatıs eski stile göre −14…−31 dB, rezonans yok; bant <600 Hz'te −3…−10 dB |
| 25.11 | İlk motor denemesi (Cf 470 pF) | Sinyal ADC sınırlarına dayandı; kart motor çalışırken resetlendi |
| 26.11 | Cf 2 nF (−12,6 dB), firmware: butonla başlatma + günlük + hata kodları | Motorda kırpılma yok; sağlam ve rulman arızalı motor net ayrıldı |

## Açık sorunlar

- **Sensör yerleri ideal değil.** Motorda X fan kapağında, Y etiket plakasında (ince parçalar), Z bir silindirin ucunda. Rulman yatağına yakın sert noktalara taşınması düşünülüyor.
- **5 kHz üstü katlanma.** Anti-alias filtresi tek kutuplu (~2,8 kHz). Arızalı motorda ve inverter anahtarlamasında 5 kHz üstündeki içerik katlanıyor olabilir.
- **Motor kalkışında bir kez tam güç kaybı (POR).** Motor inverterle sürülüyor. Kart motordan ayrı masaya alınıp powerbank'ten beslenince tekrarlanmadı.
- **Kapı açıkken SD yazma süresi ölçülmedi.** Testlerde blok kaybı olmadı.
- **TL074 çalışma noktası.** Kanal çıkışları bias'ın ~120 mV altında; MCP6004'e geçiş henüz yapılmadı.
- **Bilinen firmware hatası.** `fatfs_sd.c:320` satırında `TM_DELAY_Time2()` önünde `!` eksik. SDv1/MMC kartları (≤2 GB) etkiler, SDHC kartları etkilemez.
- **Dosya tarihleri sabit.** Kartta RTC yok; en yeni kaydı numarasından anlayın.

## Sıradaki adımlar

1. Cf ~3 nF (ilk hâle göre −16 dB) ile hoparlör testi (01.12.2026)
2. Sağlam ve arızalı motorun aynı montajla yeniden kaydı (02.12.2026); doğrulama için inverter 40 Hz'te bir kayıt
3. Öznitelik çıkarma ve arıza teşhisi (bant enerjileri, zarf spektrumu, rulman frekansları)
4. MCP6004'e geçiş, daha iyi sensör yerleri

## Firmware'i kullanma

Güncel proje `26 11 26 Cf 2nF hoparlör testi/Piezo_KaraKutu_2026-11-26.zip` içinde. STM32CubeIDE'de *File → Import → Existing Projects into Workspace* ile `Project_6_uc_Eksen_Piezo_wSPI_eg` klasörünü açıp derleyin. `Debug/` klasörü zip'te yok, CubeIDE derlerken yeniden oluşturur.

## Üçüncü taraf kod

ST HAL/CMSIS ve USB Host kütüphaneleri, Tilen Majerle'nin `tm_stm32` kütüphaneleri ve FatFs kendi lisanslarıyla dosyaların içinde yer alır.
