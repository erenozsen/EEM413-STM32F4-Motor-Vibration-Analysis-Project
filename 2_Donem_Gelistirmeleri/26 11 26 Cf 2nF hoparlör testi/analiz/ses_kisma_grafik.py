# -*- coding: utf-8 -*-
# 26.11 hoparlor ses kisma serisi (Cf 2 nF, uc piezo bantli yan yana): iki grafik
#  1) seskisik6 (kirpilmasiz): ham sinyal ust uste + frekansa gore tepe genlik
#  2) ses seviyesine gore orta piezonun (Y) ve ust/alt piezonun tepe genligi
# Kullanim: python ses_kisma_grafik.py <kayit klasoru> <cikti klasoru>
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FS = 10000
KAY = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "kayitlar"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "grafikler"
AD = ["üst piezo (X, bant)", "orta piezo (Y, bant)", "alt piezo (Z, bant)"]
RENK = ["#1f77b4", "#d62728", "#2ca02c"]


def oku(p):
    d = np.fromfile(p, dtype="<u2")
    return d[: len(d) // 3 * 3].reshape(-1, 3).astype(float)


def tepe_frekans(d, esik=15):
    """50 ms pencerelerde: sweep frekansi (en buyuk kanalin spektrum tepesi) ve her kanalin orta noktadan tepe sapmasi."""
    W = FS // 20
    med = np.median(d[: 3 * FS], axis=0)
    fr, tp = [], []
    for i in range(len(d) // W):
        s = d[i * W:(i + 1) * W]
        ac = s - s.mean(axis=0)
        if ac.std(axis=0).max() < esik:
            continue
        k = np.argmax(ac.std(axis=0))
        X = np.abs(np.fft.rfft(ac[:, k] * np.hanning(W)))
        f = np.fft.rfftfreq(W, 1 / FS)
        fr.append(f[np.argmax(X[2:]) + 2])
        tp.append(np.max(np.abs(s - med), axis=0))
    return np.array(fr), np.array(tp), med


def bant_tepe(fr, tp, kenar):
    """Frekans bantlarinda her kanalin en buyuk tepesi."""
    orta, deger = [], []
    for lo, hi in zip(kenar[:-1], kenar[1:]):
        m = (fr >= lo) & (fr < hi)
        if m.sum():
            orta.append(np.sqrt(lo * hi)); deger.append(tp[m].max(axis=0))
    return np.array(orta), np.array(deger)


# ---------- 1) seskisik6: kirpilmasiz kayit ----------
p6 = next(KAY.glob("*seskisik6*.BIN"))
d = oku(p6)
t = np.arange(len(d)) / FS
fr, tp, med = tepe_frekans(d)
fig, ax = plt.subplots(2, 1, figsize=(11, 7.5))
for k in (1, 2, 0):   # en buyuk (orta) arkada
    ax[0].plot(t, d[:, k], lw=0.3, color=RENK[k], label=AD[k])
ax[0].axhline(4095, color="k", ls="--", lw=0.8); ax[0].axhline(0, color="k", ls="--", lw=0.8)
ax[0].set_ylim(-150, 4250); ax[0].set_xlabel("zaman (s)"); ax[0].set_ylabel("ADC kodu")
ax[0].set_title("En kısık ses (6. adım), 100–5000 Hz sweep, Cf = 2 nF: hiçbir kanal sınıra dayanmıyor")
h, l = ax[0].get_legend_handles_labels()
ax[0].legend([h[l.index(a)] for a in AD], AD, loc="upper right", markerscale=20)
for k in range(3):
    ax[1].scatter(fr, tp[:, k], s=6, color=RENK[k], label=AD[k])
ax[1].axhline(4095 - med.mean(), color="k", ls="--", lw=0.8)
ax[1].text(1000, 4095 - med.mean() + 40, "üst sınıra kadar olan pay (~2200)", fontsize=9)
ax[1].set_xlim(0, 3000); ax[1].set_ylim(0, 2500)
ax[1].set_xlabel("sweep frekansı (Hz)"); ax[1].set_ylabel("orta noktadan tepe sapma (LSB)")
ax[1].set_title("Frekansa göre tepe genlik (50 ms pencereler; ~1,8 kHz üstü bu seste gürültüye yakın)")
ax[1].legend(loc="upper right", markerscale=3)
fig.tight_layout(); fig.savefig(OUT / "seskisik6_kirpilmasiz.png", dpi=130); plt.close(fig)

# ---------- 2) ses seviyesine gore tepe genlik ----------
seri = [("ses tam açık", next(KAY.glob("*sesfull*_2_*.BIN")))] + \
       [(f"{n}. kısma", next(KAY.glob(f"*seskisik{n}_*.BIN"))) for n in range(1, 7)]
kenar = np.geomspace(100, 3000, 25)
renk = plt.cm.viridis(np.linspace(0, 0.9, len(seri)))
fig, ax = plt.subplots(1, 3, figsize=(15, 5.2), sharey=True)
for j, (etiket, p) in enumerate(seri):
    fr, tp, med = tepe_frekans(oku(p))
    o, v = bant_tepe(fr, tp, kenar)
    for k in range(3):
        ax[k].plot(o, v[:, k], "o-", ms=3, lw=1.2, color=renk[j], label=etiket)
for k in range(3):
    ax[k].axhline(2200, color="k", ls="--", lw=0.8)
    ax[k].text(105, 2240, "ADC sınırı (sinyal burada kırpılır)", fontsize=8)
    ax[k].set_xscale("log"); ax[k].set_xlim(100, 3000); ax[k].set_ylim(0, 2450)
    ax[k].set_xticks([100, 200, 500, 1000, 2000, 3000]); ax[k].set_xticklabels(["100", "200", "500", "1k", "2k", "3k"])
    ax[k].set_title(AD[k]); ax[k].set_xlabel("sweep frekansı (Hz)")
ax[0].set_ylabel("bant içindeki en büyük tepe (LSB)")
ax[2].legend(loc="upper right", fontsize=8)
fig.suptitle("Hoparlör sesi adım adım kısıldıkça tepe genlik (Cf = 2 nF). Orta piezo ~200 Hz'te en son sınırdan iniyor.")
fig.tight_layout(); fig.savefig(OUT / "ses_kisma_serisi.png", dpi=130); plt.close(fig)
print("kaydedildi:", OUT / "seskisik6_kirpilmasiz.png", OUT / "ses_kisma_serisi.png")
