# -*- coding: utf-8 -*-
# 26.11 hoparlor, ses tam acik, 100-5000 Hz sweep, Cf 2 nF: ham ADC kodu ve frekansa gore tepe genlik
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FS = 10000
p, cikti = sys.argv[1], sys.argv[2]
d = np.fromfile(p, dtype="<u2"); d = d[:len(d)//3*3].reshape(-1, 3).astype(float)
t = np.arange(len(d)) / FS
renk = ["#1f77b4", "#d62728", "#2ca02c"]
ad = ["X: üst piezo (bant)", "Y: orta piezo (bant)", "Z: alt piezo (bant)"]

fig, ax = plt.subplots(2, 1, figsize=(11, 7.5))
for k in range(3):
    ax[0].plot(t, d[:, k], lw=0.3, color=renk[k], label=ad[k], alpha=0.8)
for y, s in [(4095, "4095 (üst sınır)"), (0, "0 (alt sınır)")]:
    ax[0].axhline(y, color="k", ls="--", lw=0.8)
ax[0].axhline(np.median(d[:, 0]), color="gray", ls=":", lw=0.8)
ax[0].set_ylim(-150, 4250)
ax[0].set_xlabel("zaman (s)"); ax[0].set_ylabel("ADC kodu")
ax[0].set_title("Hoparlör, ses tam açık, 100–5000 Hz sweep, Cf = 2 nF, üç piezo bantlı yan yana (ham sinyal)")
ax[0].legend(loc="upper right", markerscale=20)

# 50 ms pencerelerde baskin frekans (en buyuk kanaldan) ve tepe sapma
W = FS // 20
med = np.median(d[:int(5*FS)], axis=0)
fr, tp = [], []
for i in range(len(d) // W):
    s = d[i*W:(i+1)*W]
    ac = s - s.mean(axis=0)
    if ac.std(axis=0).max() < 60:
        continue
    k = np.argmax(ac.std(axis=0))
    X = np.abs(np.fft.rfft(ac[:, k] * np.hanning(W)))
    f = np.fft.rfftfreq(W, 1/FS)
    fr.append(f[np.argmax(X[2:]) + 2]); tp.append(np.max(np.abs(s - med), axis=0))
fr = np.array(fr); tp = np.array(tp)
for k in range(3):
    ax[1].scatter(fr, tp[:, k], s=6, color=renk[k], label=ad[k])
ax[1].axhline(4095 - med.mean(), color="k", ls="--", lw=0.8)
ax[1].text(1700, 4095 - med.mean() + 40, "üst sınıra kadar olan pay (~2200)", ha="left", fontsize=9)
ax[1].axhline(med.mean(), color="k", ls=":", lw=0.8)
ax[1].text(1700, med.mean() - 140, "alt sınıra kadar olan pay (~1900)", ha="left", fontsize=9)
ax[1].set_xlim(0, 5000); ax[1].set_ylim(0, 2500)
ax[1].set_xlabel("sweep frekansı (Hz)"); ax[1].set_ylabel("orta noktadan tepe sapma (LSB)")
ax[1].set_title("Frekansa göre tepe genlik (50 ms pencereler)")
ax[1].legend(loc="upper right", markerscale=3)
fig.tight_layout()
fig.savefig(cikti, dpi=130)
print("kaydedildi", cikti)

