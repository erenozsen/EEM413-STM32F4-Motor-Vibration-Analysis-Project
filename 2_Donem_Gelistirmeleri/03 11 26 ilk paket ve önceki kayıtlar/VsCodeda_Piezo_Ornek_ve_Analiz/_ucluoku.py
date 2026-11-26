import numpy as np
import matplotlib.pyplot as plt

# 1. Dosya Adını Belirle
dosya_adi = "PIEZO3.BIN"

# 2. Veriyi Tek Seferde Okuma
# STM32 ADC'si 12-bit okuma yapar ve bunu 16-bitlik hafızalara (uint16) yazar.
# Bu yüzden veriyi unsigned 16-bit integer olarak çekiyoruz.
tum_veri = np.fromfile(dosya_adi, dtype=np.uint16)

# 3. Veriyi "Fermuar" Mantığından Ayırma (De-interleaving)
# Gelen veri sırası: [X, Y, Z, X, Y, Z, X, Y, Z...]
piezo_x = tum_veri[0::3]  # 0. indexten başla, 3'er 3'er atlayarak al
piezo_y = tum_veri[1::3]  # 1. indexten başla, 3'er 3'er atlayarak al
piezo_z = tum_veri[2::3]  # 2. indexten başla, 3'er 3'er atlayarak al

# 4. Grafik Çizdirme Ayarları (3 Satır, 1 Sütun)
fig, axs = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
fig.suptitle('3 Eksenli Endüstriyel Titreşim Analizi', fontsize=16, fontweight='bold')

# --- 1. Piezo (X Ekseni) Grafiği ---
axs[0].plot(piezo_x, color='red', linewidth=0.8)
axs[0].set_title('X Ekseni (1. Piezo)')
axs[0].set_ylabel('ADC Değeri (0-4095)')
axs[0].grid(True, linestyle='--', alpha=0.7)

# --- 2. Piezo (Y Ekseni) Grafiği ---
axs[1].plot(piezo_y, color='green', linewidth=0.8)
axs[1].set_title('Y Ekseni (2. Piezo)')
axs[1].set_ylabel('ADC Değeri (0-4095)')
axs[1].grid(True, linestyle='--', alpha=0.7)

# --- 3. Piezo (Z Ekseni) Grafiği ---
axs[2].plot(piezo_z, color='blue', linewidth=0.8)
axs[2].set_title('Z Ekseni (3. Piezo)')
axs[2].set_xlabel('Örnek Sayısı (Zaman)')
axs[2].set_ylabel('ADC Değeri (0-4095)')
axs[2].grid(True, linestyle='--', alpha=0.7)

# Grafikleri ekrana sıkıştırmadan, düzenli bir şekilde yerleştirir
plt.tight_layout()

# Ekranda Göster
plt.show()