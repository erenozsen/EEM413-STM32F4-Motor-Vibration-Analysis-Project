import numpy as np
from scipy.io import wavfile

# 1. Dosyayı oku ve merkezle
ham_veri = np.fromfile("PIEZO.BIN", dtype=np.uint16)
merkezlenmis_veri = ham_veri.astype(np.float32) - np.mean(ham_veri)

# 2. SABİT AMFİ (Sabit Kazanç/Gain)
# Sinyali 200 kat büyütüyoruz. (Eğer ses az gelirse bu sayıyı 400 yapabilirsin)
buyutulmus_veri = merkezlenmis_veri * 200

# 3. Hoparlör patlamasın diye sınırları aşanları kırpıyoruz (Clipping)
buyutulmus_veri = np.clip(buyutulmus_veri, -32767, 32767)

# 4. Sese çevir ve kaydet
ses_verisi = buyutulmus_veri.astype(np.int16)
wavfile.write("Tek_Kanal_Sabit_Amfi.wav", 10000, ses_verisi)
print("Sabit gain uygulandı, ses oluşturuldu!")