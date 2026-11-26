# 26.11.2026, Cf = 2 nF: sağlam motor ve rulman arızalı motor (motor1) kayıtları

İlk gerçek motor veri seti. Kazanç 26.11 hoparlör testindeki gibi (Cf = 2 nF, ilk hâle göre −12,6 dB). Aynı montajla önce sağlam motor, sonra rulman/bilye arızalı motor1; ikisi de yüksüz, yarım yük ve tam yükte, her durumdan iki kayıt.

## Düzenek

- **Motorlar:** CAMAK 3 fazlı asenkron, **inverterle 50 Hz'te** sürülüyor (2 kutuplu; yüksüz ~2970 rpm). Rulmanlar **9 bilyeli**. Motor1 fazla sesli, rulman ya da bilye arızalı.
- **AFE:** TL074 (9 V pil), Cf = 2 × 1 nF film = 2 nF, Rf = 8 MΩ (alt köşe ~10 Hz), anti-alias ~2,8 kHz. 10 kHz/kanal, SPI kapısı açık.
- **Firmware:** butonla başlatma, `OLAYLAR.TXT` günlüğü, hata kodlu kırmızı LED (bkz. `26 11 26 Cf 2nF hoparlör testi`).
- **Discovery ve breadboard motordan ayrı masada**, kart powerbank'ten beslendi.

| Kanal | Pin | Yöntem | Yer | Ölçtüğü yön |
|---|---|---|---|---|
| X | PA3 | çift taraflı bant | arka fan kapağının üstü (ince sac) | düşey |
| Y | PA1 | çift taraflı bant | gövde yanındaki etiket plakası | yatay |
| Z | PA2 | mıknatıs | ön (kaplin tarafı) kapağın üstü | eksenel |

Fotoğraflar: `fotograflar/`.

## Kayıtlar (`kayitlar/`)

Biçim: `uint16` X,Y,Z,X,Y,Z… (10 kHz, ~8–10 s, motor sabit devirde). Her kanal için WAV (`_X/_Y/_Z.wav`); tüm WAV'larda **aynı kazanç** (1 LSB = 14,58, hoparlör testleriyle aynı), sağlam ve arızalı motor kulakla karşılaştırılabilir.

| Durum | Sağlam motor (`saglam_motor/`) | Arızalı motor1 (`arizali_motor1/`) | 1× (dönüş frekansı) |
|---|---|---|---|
| yüksüz | `yuksuz_…_1/2` | `yuksuz_arizali_1/2` | 49,4 Hz (~2965 rpm) |
| yarım yük | `yarimyuk_…_1/2` | `yarimyuk_arizali_1/2` | 48,2 Hz (~2890 rpm, kayma ~%3,7) |
| tam yük | `tamyuk_…_1/2` | `tamyuk_arizali_1/2` | 46,7 Hz (~2800 rpm, kayma ~%6,8) |

**Kırpılma:** sağlam motorda hiç yok (en kötü tam yükte X, payın %45'i). Arızalı motorda X ve Y'de yok; Z kayıt başına 2–86 örnekte (≤ %0,1) üst sınıra değiyor.

**Günlükler:** bütün kayıtlar butonla başlayıp durmuş, blok kaybı yok. `saglam_motor/sorunlu/` içindeki kayıt motor kalkarken kesildi: günlükte ardından gelen açılışın sebebi `GUC_ACILDI(POR)`, yani kartın beslemesi tamamen gitti (motorun inverterle kalkışı sırasında). Kart motordan ayrı masaya alındıktan sonra tekrar etmedi.

## Sonuçlar

### 1. Sağlam motor, yüke göre (`grafikler/spektrum_yuksuz_yarim_tam.png`)
- 1× yükle kayıyor (49,4 → 48,2 → 46,7 Hz); 2×, 3×, 4× onu izliyor (mekanik).
- Y ve Z'de 1× yükle büyüyor (Y 81 → 125 → 152, Z 33 → 94 → 127 LSB); X'te 2× ve 4× büyüyor.
- 100,0 Hz çizgisi 2×'ten ayrı ve sabit (elektriksel).
- 1651, 1801, 1851, 1951, 3502 Hz çizgileri yükle kaymıyor ve 50 Hz'in tam katları → inverter/elektromanyetik kaynaklı.

### 2. Sağlam ve arızalı motor (`grafikler/saglam_arizali_*.png`)
- **RMS 3–5 kat büyük** (ör. yüksüz Z 154 → 673 LSB).
- **Artış yüksek frekansta:** 45–520 Hz yalnız 1–2,5 kat; Z 2–3 kHz ~30 kat, Y 3–5 kHz 13–22 kat, X 0,5–1 kHz 5–10 kat.
- Tepe faktörü ve basıklık (kurtosis) ayırt etmiyor (ikisinde de ~3).

### 3. Rulman arıza frekansları (zarf spektrumu, 1–4,5 kHz bandı; `grafikler/saglam_arizali_zarf_spektrumu.png`)

9 bilyede BPFI + BPFO = 9 × 1×. Ölçülen BPFI'den bilye/hatve çap oranı d/D ≈ 0,200 çıkıyor (6205/6206 tipi 9 bilyeli rulmanlarda 0,203–0,207). Diğer frekanslar bu geometriden hesaplandı:

| Frekans | Hesaplanan | Ölçülen (arızalı) | Sağlam motorda |
|---|---|---|---|
| BPFI (iç bilezik) | 5,41× | **5,40×** (267,0 / 260,3 / 251,5 Hz, üç yükte de), X'te taban gürültünün ~15 katı | yok (0,4–2 LSB) |
| BPFI ± 1× yan bantları | 4,41× / 6,41× | var | yok |
| FTF (kafes) | 0,40× | **0,40–0,41×** (Z'de 37–80 LSB) | yok |
| 2×BSF (bilye) | 4,76× | **4,74×** (yüksüzde Z'de belirgin) | yok |
| BPFO (dış bilezik) | 3,59× | zayıf | yok |

Birbirinden bağımsız üç frekans (BPFI, FTF, 2×BSF) aynı rulman geometrisine uyuyor; 5,40× devirle birlikte kayıyor ve 50 Hz katı değil. **En güçlü aday iç bilezik hasarı** (BPFI ve 1× yan bantları), ikinci aday bilye hasarı (2×BSF). Dış bilezikte iz yok.

## Sınırlar

- İki farklı motor: gövde ve kaide farkı da genlikleri değiştirir (ör. Y'de 1× sağlamda 81–152, arızalıda 6–11 LSB; bu rulmanla açıklanamaz). Rulman sonucu bu yüzden genliklere değil, kesirli frekanslara dayanıyor.
- Sensör yerleri ideal değil (fan kapağı ve etiket plakası ince parçalar, Z bir silindirin ucunda); iki motorda aynı olduğu için karşılaştırma geçerli.
- Arızalı motorda Y'nin seviyesi 5 kHz'e doğru yükseliyor: 5 kHz üstündeki içerik (rulman gürültüsü ya da inverter anahtarlaması) katlanıyor olabilir.
- Sağlam motorun iki yüksüz kaydında Y farklı (1× 15 ve 119 LSB); piezo iki kayıt arasında oynamış olabilir.

## Sıradaki adım

Danışmanın isteğiyle Cf ~3 nF'a çıkarılacak (ilk hâle göre −16 dB, alt köşe ~6,6 Hz). Yeni kazançla önce hoparlör testi (01.12), sonra iki motor aynı montajla yeniden kaydedilecek (02.12); rapordaki asıl veri seti o olacak. Ek doğrulama önerisi: inverter 40 Hz'te bir kayıt (rulman çizgileri devirle, elektriksel çizgiler inverter frekansıyla kaymalı).

## Analiz betikleri (`analiz/`)

Argümansız çalıştırılırsa bu klasörün `kayitlar/` ve `grafikler/` klasörlerini kullanır. Çıktıları `*_ciktisi.txt`.

- `spektrum_yuk.py`: sağlam motorun yüke göre spektrumu ve harmonik tablosu
- `saglam_arizali.py`: RMS / tepe faktörü / basıklık, bant enerjileri, harmonikler, zarf spektrumu tepeleri ve üç grafik
- `rulman_frek.py`: 9 bilyeli rulman frekanslarında (FTF, BSF, BPFO, 2×BSF, BPFI ± 1×) zarf genliği, sağlam ve arızalı
- `motor_ozet.py <BIN> …`: tek tek kayıt özeti (süre, kırpılma, saniyelik RMS, 1× ve harmonikler)
