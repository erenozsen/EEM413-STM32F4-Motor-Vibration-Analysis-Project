import numpy as np
from scipy.io import wavfile

# 1. Dosyayı oku ve veriyi ayır
dosya_adi = "PIEZO3.BIN"
tum_veri = np.fromfile(dosya_adi, dtype=np.uint16)

# Veriyi 3 eksene ayır (De-interleaving)
piezo_x = tum_veri[0::3]
piezo_y = tum_veri[1::3]
piezo_z = tum_veri[2::3]

def sese_donustur(ham_veri, eksen_adi):
    # ADIM 1: DC Bias'ı (Sanal Toprağı) Temizle
    # Sinyalin ortalamasını alıp sinyalden çıkarıyoruz. Böylece sinyal 0'a merkezleniyor.
    merkezlenmis_veri = ham_veri.astype(np.float32) - np.mean(ham_veri)
    
    # ADIM 2: Sesi Normalize Et (Duyulabilir Seviyeye Çek)
    # Sesin çok kısık kalmaması için en yüksek tepe noktasını bulup sesi maksimum seviyeye (32767) yükseltiyoruz.
    maksimum_genlik = np.max(np.abs(merkezlenmis_veri))
    if maksimum_genlik > 0:
        normalize_veri = (merkezlenmis_veri / maksimum_genlik) * 32767
    else:
        normalize_veri = merkezlenmis_veri
        
    # ADIM 3: Standart Ses Formatına (16-bit Signed Integer) Çevir
    ses_verisi = normalize_veri.astype(np.int16)
    
    # ADIM 4: WAV Dosyası Olarak Kaydet
    # STM32 Timer ayarımız 10 kHz olduğu için örnekleme frekansını (Sample Rate) 10000 giriyoruz.
    dosya_ism = f"Titreşim_Sesi_{eksen_adi}.wav"
    wavfile.write(dosya_ism, 10000, ses_verisi)
    print(f"Başarılı! {eksen_adi} verisi sese dönüştürüldü -> {dosya_ism}")

# Fonksiyonu 3 eksen için çağır
sese_donustur(piezo_x, "X_Ekseni")
sese_donustur(piezo_y, "Y_Ekseni")
sese_donustur(piezo_z, "Z_Ekseni")