import numpy as np
import matplotlib.pyplot as plt

dosya_adi = "PIEZO.BIN"

# Verinin TAMAMINI okuyoruz
veri = np.fromfile(dosya_adi, dtype=np.uint16)

# Grafiği çizdir (Genişliği biraz artırdım ki rahat göresin)
plt.figure(figsize=(15, 5))

# [:10000] kısıtlamasını kaldırdık, tüm 'veri' dizisini veriyoruz
plt.plot(veri, color='blue', linewidth=0.5)

plt.title("Piezo Sensör Tüm Kayıt (Reset ve Vuruş Testi)")
plt.xlabel("Örneklem Sayısı (Her 10.000 örnek = 1 Saniye)")
plt.ylabel("ADC Değeri (0 - 4095)")

# Senin tespit ettiğin yeni merkez noktamız
plt.axhline(y=1860, color='red', linestyle='--', label='1.5V Merkez')

plt.legend()
plt.grid(True)
plt.show()