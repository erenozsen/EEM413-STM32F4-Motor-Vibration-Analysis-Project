/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "spi.h"
#include "tim.h"
#include "usb_host.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "fatfs_sd.h"
#include "string.h"
#include "tm_stm32_fatfs.h"
#include "tm_stm32_delay.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
// Örnekleme: TIM3 = 84 MHz / 84 / 100 = 10 kHz (her tetikte 3 kanal birden)
#define NUM_CHANNELS       3
#define SAMPLE_RATE_HZ     10000
#define FRAMES_PER_HALF    4096                                  // yarı başına 409.6 ms
#define HALF_SIZE          (NUM_CHANNELS * FRAMES_PER_HALF)      // yarıdaki örnek sayısı
#define BUFFER_SIZE        (2 * HALF_SIZE)                       // 24576 örnek = 48 KB
#define HALF_BYTES         (HALF_SIZE * sizeof(uint16_t))        // 24576 byte = 48 sektör
#define HALF_PERIOD_MS     (FRAMES_PER_HALF * 1000 / SAMPLE_RATE_HZ)
#define SYNC_EVERY_HALVES  2      // f_sync ~0.8 s'de bir (her blokta değil)
#define STALL_TIMEOUT_MS   (3 * HALF_PERIOD_MS)  // bu süre DMA kesmesi gelmezse ADC durmuştur

// Mount sonrası SD SPI hızı: 84 MHz / 8 = 10.5 MHz.
// Kablolar uzunsa ve yazma hatası (kırmızı LED) görülürse SPI_BAUDRATEPRESCALER_16 deneyin.
#define SD_SPI_FAST_PRESCALER  SPI_BAUDRATEPRESCALER_8

#define LED_PORT    GPIOD
#define LED_GREEN   LD4_Pin   // Yeşil: kayıt sürüyor
#define LED_ORANGE  LD3_Pin   // Turuncu: kayıt durdu, dosya kapandı (kart çıkarılabilir)
#define LED_RED     LD5_Pin   // Kırmızı: yeşil yanarken sabit = VERİ KAYBI; yeşil sönükken YANIP SÖNER = HATA
// Hata kodları (26.11.2026): kırmızı LED kod kadar kısa yanıp söner, 1,5 s bekler, tekrarlar.
//   1 = SD kart bağlanamadı (mount)        2 = SD'ye yazma hatası veya kart dolu
//   3 = ADC/DMA hatası                     4 = ADC durdu (örnek gelmiyor)
//   5 = dosya açılamadı / kapatılamadı
#define HATA_MOUNT   1
#define HATA_YAZMA   2
#define HATA_ADC     3
#define HATA_DURMA   4
#define HATA_DOSYA   5
#define LED_BLUE    LD6_Pin   // Mavi: her blok karta yazıldığında yanıp söner
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
FATFS fs;
FIL fil;
FRESULT fres;
UINT bytesWrote;

// 3 kanal x 4096 örnek x 2 (Ping-Pong Buffer)
uint16_t adc_buffer[BUFFER_SIZE];

// DMA kesmelerini kontrol edeceğimiz bayrak (0: Bekle, 1: İlk Yarı, 2: İkinci Yarı)
volatile uint8_t write_flag = 0;
volatile uint32_t last_half_tick = 0;   // son DMA yarı kesmesinin zamanı (ms)
volatile uint32_t overrun_count = 0;    // kaybolan/bozulan blok sayısı (0 olmalı)
volatile uint8_t adc_error = 0;

typedef enum { REC_IDLE, REC_RUNNING, REC_FAULT } RecState;
RecState rec_state = REC_IDLE;
char file_name[13];                     // "PIEZO001.BIN" (8.3 isim, LFN kapalı)
uint32_t halves_since_sync = 0;
static uint8_t hata_kodu = 0;               // kırmızı LED yanıp sönme sayısı (yukarıdaki tablo)
static char hata_detay[32];                 // hangi SD işlemi hangi FatFs koduyla bozuldu, ör. "f_sync FR=1"
static const char *bekleyen_acilis = NULL;  // açılışta SD bağlanamadıysa reset sebebi sonra yazılır
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
void MX_USB_HOST_Process(void);

/* USER CODE BEGIN PFP */
static void SD_SPI_SetFast(void);
static FRESULT Recording_Start(void);
static uint8_t Recording_WritePending(void);
static void Recording_Stop(void);
static void Recording_Fault(uint8_t kod, const char *neden);
static uint8_t Button_Pressed(void);
static const char *Reset_Sebebi(void);
static FRESULT Olay_Yaz(const char *metin, const char *ek);
static FRESULT SD_Bagla(uint8_t kez, uint8_t *kacinci);
static void Hata_Detay(const char *islem, FRESULT r);
static void Sayi_Ekle(char *s, uint32_t n);
static void Hata_LED(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_SPI1_Init();
  MX_USB_HOST_Init();
  MX_TIM3_Init();
  /* USER CODE BEGIN 2 */
  // Reset sebebini SD işlemlerinden önce oku ve bayrakları temizle (25.11.2026)
  const char *reset_sebebi = Reset_Sebebi();
  HAL_Delay(500); // Sistemin ve SD kartın güç alıp oturması için kısa bir mola

    // 1. SD Kartı Sisteme Bağla (Mount) - başlatma yavaş SPI ile yapılır (defines.h).
    //    İlk denemede olmazsa 3 kez dener (26.11.2026).
    uint8_t kacinci = 0;
    fres = SD_Bagla(3, &kacinci);
    if(fres != FR_OK) {
        bekleyen_acilis = reset_sebebi;   // SD sonradan bağlanırsa bu açılış da günlüğe yazılır
        Hata_Detay("f_mount", fres);
        Recording_Fault(HATA_MOUNT, "SD baglanamadi (acilis)");
    } else {
        Olay_Yaz("ACILIS, reset sebebi:", reset_sebebi);
        if(kacinci > 1) {
            char k[2] = { (char)('0' + kacinci), '\0' };
            Olay_Yaz("SD ancak su denemede baglandi:", k);
        }

        // 2. Kayıt açılışta KENDİLİĞİNDEN BAŞLAMAZ (25.11.2026). Turuncu LED = hazır;
        //    mavi butona basınca kayıt başlar. Motor çalışırken kart resetlenirse
        //    kendi kendine yeni dosyalar açılmasın diye.
        rec_state = REC_IDLE;
        HAL_GPIO_WritePin(LED_PORT, LED_ORANGE, GPIO_PIN_SET);
    }
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if(rec_state == REC_RUNNING) {
	      // Dolan yarıyı karta yaz
	      if(!Recording_WritePending()) {
	          Recording_Fault(HATA_YAZMA, "SD yazma hatasi veya kart dolu"); // ayrıntı hata_detay'da
	      } else {
	          // Önce last_half_tick'i oku, sonra şimdiki zamanı (kesme ile yarış olmasın)
	          uint32_t last = last_half_tick;
	          if(adc_error) {
	              Recording_Fault(HATA_ADC, "ADC/DMA hatasi");
	          } else if((HAL_GetTick() - last) > STALL_TIMEOUT_MS) {
	              Recording_Fault(HATA_DURMA, "ADC durdu (ornek gelmiyor)");
	          } else if(Button_Pressed()) {
	              Recording_Stop(); // Mavi butona basıldı: dosyayı düzgünce kapat
	          }
	      }
	      if(overrun_count != 0) {
	          HAL_GPIO_WritePin(LED_PORT, LED_RED, GPIO_PIN_SET); // Veri kaybı oldu
	      }
	  } else if(rec_state == REC_IDLE) {
	      // Kayıt durmuşken butona basılırsa yeni dosyaya yeni kayıt başlat
	      if(Button_Pressed()) {
	          FRESULT r = Recording_Start();
	          if(r != FR_OK) {
	              Hata_Detay("dosya acma", r);
	              Recording_Fault(HATA_DOSYA, "dosya acilamadi");
	          }
	      }
	  } else if(rec_state == REC_FAULT) {
	      Hata_LED(); // kırmızı LED hata kodu kadar yanıp söner
	      // Hatadan sonra butona basılırsa kartı yeniden bağlayıp yeni kayda başlamayı dene
	      // (25.11.2026). Olmazsa kırmızı yanıp sönmeye devam eder; o zaman gücü kesip yeniden ver.
	      if(Button_Pressed()) {
	          uint8_t k = 0;
	          hata_detay[0] = '\0';
	          fres = SD_Bagla(3, &k);
	          if(fres == FR_OK) {
	              if(bekleyen_acilis != NULL) {
	                  Olay_Yaz("ACILIS (SD sonradan baglandi), reset sebebi:", bekleyen_acilis);
	                  bekleyen_acilis = NULL;
	              }
	              Olay_Yaz("hatadan sonra butonla yeniden baslatma", "");
	              FRESULT r = Recording_Start();
	              if(r != FR_OK) {
	                  Hata_Detay("dosya acma", r);
	                  Recording_Fault(HATA_DOSYA, "yeniden baslatma: dosya acilamadi");
	              }
	          } else {
	              Hata_Detay("f_mount", fres);
	              Recording_Fault(HATA_MOUNT, "yeniden baslatma: SD baglanamadi");
	          }
	      }
	  }
    /* USER CODE END WHILE */
    MX_USB_HOST_Process();

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 7;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
// Mount sonrası SPI'ı hızlandır (başlatma 328 kHz ile yapıldı, bkz. defines.h)
static void SD_SPI_SetFast(void) {
    while(FATFS_SPI->SR & SPI_SR_BSY); // Son byte'ın gitmesini bekle
    CLEAR_BIT(FATFS_SPI->CR1, SPI_CR1_SPE);
    MODIFY_REG(FATFS_SPI->CR1, SPI_CR1_BR, SD_SPI_FAST_PRESCALER);
    SET_BIT(FATFS_SPI->CR1, SPI_CR1_SPE);
}

// İlk kullanılmamış PIEZOnnn.BIN dosyasını açar ve örneklemeyi başlatır.
// Eski kayıtların üzerine asla yazılmaz.
static FRESULT Recording_Start(void) {
    FILINFO fno;
    FRESULT res = FR_DENIED; // 999 dosyanın hepsi doluysa

    for(uint16_t n = 1; n <= 999; n++) {
        memcpy(file_name, "PIEZO000.BIN", sizeof(file_name));
        file_name[5] = '0' + (n / 100);
        file_name[6] = '0' + (n / 10) % 10;
        file_name[7] = '0' + (n % 10);
        res = f_stat(file_name, &fno);
        if(res == FR_NO_FILE) break;  // Bu isim boş, bunu kullan
        if(res != FR_OK) return res;  // Kart okuma hatası
        res = FR_DENIED;
    }
    if(res != FR_NO_FILE) return res;

    res = f_open(&fil, file_name, FA_WRITE | FA_CREATE_NEW);
    if(res != FR_OK) return res;

    // Dosya başlığını fiziksel olarak karta kazı ki Windows görebilsin
    f_sync(&fil);
    Olay_Yaz("kayit basladi:", file_name); // örnekleme başlamadan önce, kayda gecikme katmasın

    write_flag = 0;
    adc_error = 0;
    overrun_count = 0;
    halves_since_sync = 0;
    last_half_tick = HAL_GetTick();

    // DMA ve Timer'ı Başlat (Veri akışı başlıyor)
    if(HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, BUFFER_SIZE) != HAL_OK ||
       HAL_TIM_Base_Start(&htim3) != HAL_OK) {
        f_close(&fil);
        return FR_INT_ERR;
    }

    rec_state = REC_RUNNING;
    HAL_GPIO_WritePin(LED_PORT, LED_ORANGE | LED_RED, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_PORT, LED_GREEN, GPIO_PIN_SET);
    return FR_OK;
}

// Dolmuş bir yarı varsa karta yazar. Hata olursa 0, aksi halde 1 döner.
static uint8_t Recording_WritePending(void) {
    // Bayrağı yazmadan ÖNCE indir: yazma sürerken diğer yarı dolarsa
    // kesmenin koyduğu bayrak silinmesin (eskiden o blok sessizce kayboluyordu)
    __disable_irq();
    uint8_t half = write_flag;
    write_flag = 0;
    __enable_irq();
    if(half == 0) return 1;

    uint16_t *src = (half == 1) ? &adc_buffer[0] : &adc_buffer[HALF_SIZE];
    fres = f_write(&fil, src, HALF_BYTES, &bytesWrote);
    if(fres != FR_OK) { Hata_Detay("f_write", fres); return 0; }  // Yazma hatası
    if(bytesWrote != HALF_BYTES) { Hata_Detay("kart dolu", fres); return 0; }

    // Yazma sürerken diğer yarı da dolduysa DMA bu yarının üzerine yazmaya
    // başlamıştır: blok bozulmuş olabilir
    if(write_flag != 0) overrun_count++;

    // Elektrik kesilirse veriler kaybolmasın diye periyodik olarak kalıcı kaydet
    if(++halves_since_sync >= SYNC_EVERY_HALVES) {
        halves_since_sync = 0;
        fres = f_sync(&fil);
        if(fres != FR_OK) { Hata_Detay("f_sync", fres); return 0; }
    }

    HAL_GPIO_TogglePin(LED_PORT, LED_BLUE); // Mavi LED'i tersle (Göz kırpma)
    return 1;
}

// Örneklemeyi durdurur, kalan veriyi yazar ve dosyayı kapatır.
static void Recording_Stop(void) {
    HAL_TIM_Base_Stop(&htim3);
    HAL_Delay(2); // Son taramanın (3 kanal ~22 us) bitmesini bekle
    uint32_t pos = BUFFER_SIZE - __HAL_DMA_GET_COUNTER(hadc1.DMA_Handle);
    HAL_ADC_Stop_DMA(&hadc1);

    // Önce dolmuş ama henüz yazılmamış yarıyı, sonra yarım kalan bloğu yaz
    uint8_t ok = Recording_WritePending();
    uint32_t start = (pos >= HALF_SIZE) ? HALF_SIZE : 0;
    uint32_t count = ((pos - start) / NUM_CHANNELS) * NUM_CHANNELS; // tam frame'ler
    if(ok && count > 0) {
        FRESULT r = f_write(&fil, &adc_buffer[start], count * sizeof(uint16_t), &bytesWrote);
        if(r != FR_OK) { Hata_Detay("son f_write", r); ok = 0; }
    }

    fres = f_close(&fil);
    if(fres != FR_OK) Hata_Detay("f_close", fres);
    rec_state = REC_IDLE;
    HAL_GPIO_WritePin(LED_PORT, LED_GREEN | LED_BLUE, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_PORT, LED_ORANGE, GPIO_PIN_SET);
    if(!ok || fres != FR_OK) {
        Recording_Fault(ok ? HATA_DOSYA : HATA_YAZMA, "durdurma: son blok yazilamadi veya dosya kapanmadi");
    } else {
        Olay_Yaz("kayit butonla durduruldu, kayip blok:", overrun_count ? "VAR" : "yok");
    }
}

// Ciddi hata: örneklemeyi durdur, o ana kadarki veriyi kurtarmaya çalış, kırmızı LED.
// Sebep (ve varsa hangi SD işleminin hangi kodla bozulduğu) OLAYLAR.TXT'ye yazılır. SD o an
// yazılamıyorsa kart bir kez yeniden bağlanıp tekrar denenir (26.11.2026); yine olmazsa
// sebep yalnız kırmızı LED'in yanıp sönme sayısından okunur.
static void Recording_Fault(uint8_t kod, const char *neden) {
    static char ek[96];           // neden (≤50) + " (" + hata_detay (≤31) + ")"
    if(rec_state == REC_RUNNING) {
        HAL_TIM_Base_Stop(&htim3);
        HAL_ADC_Stop_DMA(&hadc1);
        f_close(&fil);
    }
    rec_state = REC_FAULT;
    hata_kodu = kod;
    HAL_GPIO_WritePin(LED_PORT, LED_GREEN | LED_ORANGE | LED_BLUE, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_PORT, LED_RED, GPIO_PIN_SET);

    ek[0] = '\0';
    strncat(ek, neden, 50);
    if(hata_detay[0] != '\0') {
        strcat(ek, " (");
        strncat(ek, hata_detay, sizeof(hata_detay) - 1);
        strcat(ek, ")");
    }
    if(Olay_Yaz("HATA:", ek) != FR_OK) {
        uint8_t k = 0;
        if(SD_Bagla(2, &k) == FR_OK) {
            if(bekleyen_acilis != NULL) {
                Olay_Yaz("ACILIS (SD sonradan baglandi), reset sebebi:", bekleyen_acilis);
                bekleyen_acilis = NULL;
            }
            Olay_Yaz("HATA (SD yeniden baglanip yazildi):", ek);
        }
    }
}

// SD kartı (yeniden) bağlar: en çok 'kez' deneme, aralarında 300 ms. Başarılıysa SPI'ı
// hızlandırır ve kaçıncı denemede bağlandığını *kacinci'ye yazar. f_mount kartı her seferinde
// yavaş SPI ile baştan başlatır (fatfs_sd.c).
static FRESULT SD_Bagla(uint8_t kez, uint8_t *kacinci) {
    FRESULT r = FR_NOT_READY;
    for(uint8_t i = 1; i <= kez; i++) {
        f_mount(NULL, "", 0);
        r = f_mount(&fs, "", 1);
        if(r == FR_OK) {
            SD_SPI_SetFast();
            *kacinci = i;
            return FR_OK;
        }
        HAL_Delay(300);
    }
    return r;
}

// "f_sync FR=1" gibi kısa bir ayrıntı saklar. FR kodları (ff.h): 1 = DISK_ERR (SD cevap vermedi
// veya yazmayı reddetti), 3 = NOT_READY (SD başlatılamadı), 9 = INVALID_OBJECT, 13 = NO_FILESYSTEM.
static void Hata_Detay(const char *islem, FRESULT r) {
    hata_detay[0] = '\0';
    strncat(hata_detay, islem, 20);
    strcat(hata_detay, " FR=");
    Sayi_Ekle(hata_detay, (uint32_t)r);
}

// s'nin sonuna n'yi ondalık yazar (printf kullanmadan).
static void Sayi_Ekle(char *s, uint32_t n) {
    char sayi[11];
    int i = 9;
    sayi[10] = '\0';
    do { sayi[i--] = (char)('0' + (n % 10)); n /= 10; } while(n && i >= 0);
    strcat(s, &sayi[i + 1]);
}

// REC_FAULT'ta ana döngüden çağrılır: kırmızı LED hata_kodu kadar 250 ms yanar / 250 ms söner,
// ardından 1,5 s sönük kalır ve tekrarlar. Bekleme yok, buton okunmaya devam eder.
static void Hata_LED(void) {
    if(hata_kodu == 0) return;
    uint32_t yanip = (uint32_t)hata_kodu * 500;
    uint32_t t = HAL_GetTick() % (yanip + 1500);
    GPIO_PinState s = (t < yanip && (t % 500) < 250) ? GPIO_PIN_SET : GPIO_PIN_RESET;
    HAL_GPIO_WritePin(LED_PORT, LED_RED, s);
}

// RCC_CSR'deki reset bayraklarını okuyup temizler. Güç verildiğinde POR+PIN(+BOR) birlikte
// gelir; yalnız BOR = besleme düştü (ör. motor çalışırken), IWDG/WWDG = bekçi, SFT = yazılım.
static const char *Reset_Sebebi(void) {
    static char s[48];
    uint32_t csr = RCC->CSR;
    s[0] = '\0';
    if(csr & RCC_CSR_LPWRRSTF) strcat(s, "LPWR ");
    if(csr & RCC_CSR_WWDGRSTF) strcat(s, "WWDG ");
    if(csr & RCC_CSR_IWDGRSTF) strcat(s, "IWDG ");
    if(csr & RCC_CSR_SFTRSTF)  strcat(s, "YAZILIM ");
    if(csr & RCC_CSR_PORRSTF)  strcat(s, "GUC_ACILDI(POR) ");
    if(csr & RCC_CSR_BORRSTF)  strcat(s, "BESLEME_DUSTU(BOR) ");
    if(csr & RCC_CSR_PINRSTF)  strcat(s, "NRST_PINI ");
    if(s[0] == '\0') strcat(s, "bilinmiyor");
    RCC->CSR |= RCC_CSR_RMVF; // bayrakları temizle, bir sonraki reset temiz okunsun
    return s;
}

// OLAYLAR.TXT'nin sonuna "[açılıştan beri saniye] metin ek" satırı ekler. Kayıt akışını
// durdurmaz; yazılamazsa yalnız FR kodunu döndürür (Recording_Fault bunu kullanır).
// Saat (RTC) olmadığı için zaman açılıştan itibaren saniye; ACILIS satırları yeni açılışı gösterir.
static FRESULT Olay_Yaz(const char *metin, const char *ek) {
    static FIL olay_fil;          // FIL ~550 bayt; yığında değil, statik
    static char satir[180];
    UINT yazilan;
    satir[0] = '\0';
    strcat(satir, "[");
    Sayi_Ekle(satir, HAL_GetTick() / 1000);
    strcat(satir, " s] ");
    strncat(satir, metin, 60);
    strcat(satir, " ");
    strncat(satir, ek, 90);
    strcat(satir, "\r\n");
    FRESULT r = f_open(&olay_fil, "OLAYLAR.TXT", FA_OPEN_APPEND | FA_WRITE);
    if(r != FR_OK) return r;
    r = f_write(&olay_fil, satir, strlen(satir), &yazilan);
    FRESULT rc = f_close(&olay_fil);
    return (r != FR_OK) ? r : rc;
}

// Mavi buton (B1, PA0): basılınca HIGH. Debounce'lu, yalnızca basma anında 1 döner.
static uint8_t Button_Pressed(void) {
    static uint8_t stable = 0, last_raw = 0;
    static uint32_t change_tick = 0;
    uint8_t raw = (HAL_GPIO_ReadPin(B1_GPIO_Port, B1_Pin) == GPIO_PIN_SET);
    uint32_t now = HAL_GetTick();

    if(raw != last_raw) {
        last_raw = raw;
        change_tick = now;
    }
    if(raw != stable && (now - change_tick) >= 30) {
        stable = raw;
        return stable;
    }
    return 0;
}

// DMA dizinin İLK YARISINI doldurduğunda donanım otomatik olarak buraya zıplar
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc) {
    if(hadc->Instance == ADC1) {
        if(write_flag != 0) overrun_count++; // Önceki yarı hiç yazılamadı, kayboldu
        write_flag = 1;
        last_half_tick = HAL_GetTick();
    }
}

// DMA dizinin TAMAMINI doldurduğunda donanım otomatik olarak buraya zıplar
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    if(hadc->Instance == ADC1) {
        if(write_flag != 0) overrun_count++; // Önceki yarı hiç yazılamadı, kayboldu
        write_flag = 2;
        last_half_tick = HAL_GetTick();
    }
}

// ADC/DMA hatası (ör. DMA transfer hatası)
void HAL_ADC_ErrorCallback(ADC_HandleTypeDef* hadc) {
    if(hadc->Instance == ADC1) {
        adc_error = 1;
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
