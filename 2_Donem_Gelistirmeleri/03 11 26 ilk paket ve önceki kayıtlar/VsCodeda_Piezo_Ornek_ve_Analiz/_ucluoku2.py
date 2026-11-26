import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ================= AYARLAR =================
dosya_adi = "PIEZO001.BIN"  # SD karttan aldığın son dosyanın adı
ornekleme_frekansi = 10000  # 10 kHz
# ===========================================

# 1. Veriyi Oku ve Ayır
print("Veriler okunuyor, lütfen bekleyin...")
tum_veri = np.fromfile(dosya_adi, dtype=np.uint16)

piezo_x = tum_veri[0::3]
piezo_y = tum_veri[1::3]
piezo_z = tum_veri[2::3]

# 2. Zaman eksenini oluştur (Saniye cinsinden)
toplam_ornek = len(piezo_x)
zaman = np.arange(toplam_ornek) / ornekleme_frekansi

# 3. İnteraktif Plotly Alt Grafikleri (Subplots) Oluşturma
# Tüm eksenlerin X (zaman) ekseni birbirine kilitli olacak (shared_xaxes=True)
# Yani birine zoom yapınca diğerleri de aynı saniyeye zoom yapacak.
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=('X Ekseni (1. Piezo)', 'Y Ekseni (2. Piezo)', 'Z Ekseni (3. Piezo)'))

# WebGL (Scattergl) kullanarak yüz binlerce noktanın kasmadan, yağ gibi akmasını sağlıyoruz
fig.add_trace(go.Scattergl(x=zaman, y=piezo_x, mode='lines', name='X Ekseni', 
                           line=dict(color='red', width=1)), row=1, col=1)

fig.add_trace(go.Scattergl(x=zaman, y=piezo_y, mode='lines', name='Y Ekseni', 
                           line=dict(color='green', width=1)), row=2, col=1)

fig.add_trace(go.Scattergl(x=zaman, y=piezo_z, mode='lines', name='Z Ekseni', 
                           line=dict(color='blue', width=1)), row=3, col=1)

# 4. Arayüz ve Tasarım Ayarları
fig.update_layout(
    title='3 Eksenli İnteraktif Titreşim Analizi (Zoom İçin Fare ile Seçin / Çift Tıklayarak Geri Dönün)',
    hovermode='x unified', # Fareyi gezdirdiğinde 3 eksenin o anki değerini aynı anda gösterir
    height=900,
    showlegend=False
)

fig.update_xaxes(title_text="Zaman (Saniye)", row=3, col=1)
fig.update_yaxes(title_text="ADC Değeri", row=1, col=1)
fig.update_yaxes(title_text="ADC Değeri", row=2, col=1)
fig.update_yaxes(title_text="ADC Değeri", row=3, col=1)

# Grafiği Tarayıcıda Aç
print("Grafik hazırlanıyor...")
fig.show(renderer="browser")