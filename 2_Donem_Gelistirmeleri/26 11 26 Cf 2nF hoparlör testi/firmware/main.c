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
#define LED_RED     LD5_Pin   // Kırmızı: yeşil sönükse HATA, yeşil yanıyorsa VERİ KAYBI oldu
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
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
void MX_USB_HOST_Process(void);

/* USER CODE BEGIN PFP */
static void SD_SPI_SetFast(void);
static FRESULT Recording_Start(void);
static uint8_t Recording_WritePending(void);
static void Recording_Stop(void);
static void Recording_Fault(const char *neden);
static uint8_t Button_Pressed(void);
static const char *Reset_Sebebi(void);
static void Olay_Yaz(const char *metin, const char *ek);
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

    // 1. SD Kartı Sisteme Bağla (Mount) - başlatma yavaş SPI ile yapılır (defines.h)
    fres = f_mount(&fs, "", 1);
    if(fres != FR_OK) {
        Recording_Fault("mount hatasi"); // Kırmızı LED (Mount Hatası)
    } else {
        SD_SPI_SetFast();
        Olay_Yaz("ACILIS, reset sebebi:", reset_sebebi);

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
	          Recording_Fault("yazma hatasi veya kart dolu"); // Yazma hatası veya kart dolu
	      } else {
	          // Önce last_half_tick'i oku, sonra şimdiki zamanı (kesme ile yarış olmasın)
	          uint32_t last = last_half_tick;
	          if(adc_error) {
	              Recording_Fault("ADC/DMA hatasi");
	          } else if((HAL_GetTick() - last) > STALL_TIMEOUT_MS) {
	              Recording_Fault("ADC durdu (ornek gelmiyor)");
	          } else if(Button_Pressed()) {
	              Recording_Stop(); // Mavi butona basıldı: dosyayı düzgünce kapat
	          }
	      }
	      if(overrun_count != 0) {
	          HAL_GPIO_WritePin(LED_PORT, LED_RED, GPIO_PIN_SET); // Veri kaybı oldu
	      }
	  } else if(rec_state == REC_IDLE) {
	      // Kayıt durmuşken butona basılırsa yeni dosyaya yeni kayıt başlat
	      if(Button_Pressed() && Recording_Start() != FR_OK) {
	          Recording_Fault("dosya acilamadi");
	      }
	  } else if(rec_state == REC_FAULT) {
	      // Hatadan sonra butona basılırsa kartı yeniden bağlayıp yeni kayda başlamayı dene
	      // (25.11.2026). Olmazsa kırmızı yanık kalır; o zaman gücü kesip yeniden ver.
	      if(Button_Pressed()) {
	          f_mount(NULL, "", 0);
	          fres = f_mount(&fs, "", 1);
	          if(fres == FR_OK) {
	              SD_SPI_SetFast();
	              Olay_Yaz("hatadan sonra butonla yeniden baslatma", "");
	              if(Recording_Start() != FR_OK) Recording_Fault("yeniden baslatma: dosya acilamadi");
	          } else {
	              Recording_Fault("yeniden baslatma: mount hatasi");
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
    if(fres != FR_OK || bytesWrote != HALF_BYTES) return 0; // Yazma hatası veya kart dolu

    // Yazma sürerken diğer yarı da dolduysa DMA bu yarının üzerine yazmaya
    // başlamıştır: blok bozulmuş olabilir
    if(write_flag != 0) overrun_count++;

    // Elektrik kesilirse veriler kaybolmasın diye periyodik olarak kalıcı kaydet
    if(++halves_since_sync >= SYNC_EVERY_HALVES) {
        halves_since_sync = 0;
        fres = f_sync(&fil);
        if(fres != FR_OK) return 0;
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
        ok = (f_write(&fil, &adc_buffer[start], count * sizeof(uint16_t), &bytesWrote) == FR_OK);
    }

    fres = f_close(&fil);
    rec_state = REC_IDLE;
    HAL_GPIO_WritePin(LED_PORT, LED_GREEN | LED_BLUE, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_PORT, LED_ORANGE, GPIO_PIN_SET);
    if(!ok || fres != FR_OK) {
        Recording_Fault("durdurma: son blok yazilamadi veya dosya kapanmadi");
    } else {
        Olay_Yaz("kayit butonla durduruldu, kayip blok:", overrun_count ? "VAR" : "yok");
    }
}

// Ciddi hata: örneklemeyi durdur, o ana kadarki veriyi kurtarmaya çalış, kırmızı LED.
// Sebep OLAYLAR.TXT'ye yazılır (kart hâlâ yazılabiliyorsa).
static void Recording_Fault(const char *neden) {
    if(rec_state == REC_RUNNING) {
        HAL_TIM_Base_Stop(&htim3);
        HAL_ADC_Stop_DMA(&hadc1);
        f_close(&fil);
    }
    rec_state = REC_FAULT;
    HAL_GPIO_WritePin(LED_PORT, LED_GREEN | LED_ORANGE | LED_BLUE, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_PORT, LED_RED, GPIO_PIN_SET);
    Olay_Yaz("HATA:", neden);
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

// OLAYLAR.TXT'nin sonuna "[açılıştan beri saniye] metin ek" satırı ekler. Hata olursa sessizce geçer.
// Saat (RTC) olmadığı için zaman açılıştan itibaren saniye; ACILIS satırları yeni açılışı gösterir.
static void Olay_Yaz(const char *metin, const char *ek) {
    static FIL olay_fil;          // FIL ~550 bayt; yığında değil, statik
    static char satir[160];
    char sayi[12];
    UINT yazilan;
    uint32_t sn = HAL_GetTick() / 1000;
    int i = 10;
    sayi[11] = '\0';
    do { sayi[i--] = '0' + (sn % 10); sn /= 10; } while(sn && i >= 0);
    satir[0] = '\0';
    strcat(satir, "[");
    strcat(satir, &sayi[i + 1]);
    strcat(satir, " s] ");
    strncat(satir, metin, 60);
    strcat(satir, " ");
    strncat(satir, ek, 50);
    strcat(satir, "\r\n");
    if(f_open(&olay_fil, "OLAYLAR.TXT", FA_OPEN_APPEND | FA_WRITE) != FR_OK) return;
    f_write(&olay_fil, satir, strlen(satir), &yazilan);
    f_close(&olay_fil);
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
