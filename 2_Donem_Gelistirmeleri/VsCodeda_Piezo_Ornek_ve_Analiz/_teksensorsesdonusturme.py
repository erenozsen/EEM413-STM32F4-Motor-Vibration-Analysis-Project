import numpy as np
from scipy.io import wavfile

# Dosyayı doğrudan tek kanal olarak oku
ham_veri = np.fromfile("PIEZO.BIN", dtype=np.uint16)

# Ayırma (de-interleave) YAPMIYORUZ, veriyi doğrudan sese çeviriyoruz
merkezlenmis_veri = ham_veri.astype(np.float32) - np.mean(ham_veri)
maksimum_genlik = np.max(np.abs(merkezlenmis_veri))

if maksimum_genlik > 0:
    normalize_veri = (merkezlenmis_veri / maksimum_genlik) * 32767
else:
    normalize_veri = merkezlenmis_veri
    
ses_verisi = normalize_veri.astype(np.int16)
wavfile.write("Tek_Kanal_Test_Sesi.wav", 10000, ses_verisi)
print("Tek kanal test sesi oluşturuldu!")