# -*- coding: utf-8 -*-
# 18.11 aksam sweep kayitlari icin danisman grafikleri. Kayitlara yazmaz.
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
BURA = Path(sys.argv[0]).resolve().parent
KOK = Path(__file__).resolve().parents[1] / "kayitlar"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else BURA; OUT.mkdir(parents=True, exist_ok=True)
FS = 10000
d = np.load(BURA / "frek_tepki.npz")
FK = d["FK"]

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as tk
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "grid.color": "#e4e3df", "legend.frameon": False})
MAV, TUR, YES, SAR = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
# renk = yontem (tum grafiklerde sabit): eski stil yesil, miknatis turuncu, bant sari, referans Y mavi


def oku(ad):
    x = np.fromfile(KOK / ad, dtype=np.uint16)
    v = x[: len(x) // 3 * 3].reshape(-1, 3).T.astype(float)
    return v - np.median(v, axis=1, keepdims=True)


# 1) Ayni noktada uc yontem: sinyal / referans Y
fig, ax = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
for anahtar, et, renk in (("XY_B", "Eski stil (yapışkan) — kayıt B, X piezosu", YES),
                          ("XY_C", "Çift taraflı bant — kayıt C, aynı X piezosu", SAR),
                          ("ZY_A", "Mıknatıslı — kayıt A, Z piezosu", TUR)):
    ax[0].plot(FK, d[anahtar], "-o", ms=4, lw=2, color=renk, label=et)
ax[0].set_yscale("log")
ax[0].yaxis.set_major_locator(tk.FixedLocator([0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5]))
ax[0].yaxis.set_major_formatter(tk.FormatStrFormatter("%g")); ax[0].yaxis.set_minor_formatter(tk.NullFormatter())
ax[0].set_ylabel("Sensör sinyali / referans Y sinyali")
ax[0].set_title("Aynı noktada üç montaj yöntemi (referans: hiç oynatılmayan Y piezosu)", loc="left")
ax[0].legend(loc="lower left", fontsize=10); ax[0].grid(True, which="major")
for anahtar, et, renk in (("T", "Çift taraflı bant / eski stil (aynı piezo, aynı kanal)", SAR),
                          ("M", "Mıknatıslı / eski stil (farklı piezo ve kanal; eğri ±%30 kayabilir)", TUR)):
    ax[1].plot(FK, 20 * np.log10(d[anahtar]), "-o", ms=4, lw=2, color=renk, label=et)
ax[1].axhline(0, color="#52514e", lw=0.8)
ax[1].text(110, 1.2, "0 dB = eski stil ile aynı", color="#52514e", fontsize=9)
ax[1].set_ylabel("Eski stile göre (dB)"); ax[1].set_xlabel("Frekans (Hz)")
ax[1].set_title("Montaj yöntemlerinin frekans tepkisi, eski stile göre", loc="left")
ax[1].set_ylim(-45, 15); ax[1].grid(True); ax[1].legend(loc="lower left", fontsize=10)
ax[1].text(0.99, 0.03, "Boşluklar: o frekansta sinyal ADC sınırına dayandı (kırpıldı), ölçülemedi",
           transform=ax[1].transAxes, ha="right", fontsize=9, color="#52514e")
fig.tight_layout(); fig.savefig(OUT / "1_frekans_tepkisi_uc_yontem.png", dpi=110); plt.close(fig)

# 2) Her kayittan bir yukari tarama, ham sinyaller ust uste (x ekseni frekans)
TAR = {"A": ("A_miknatisli_PIEZO001.BIN", 13.35, 17.45), "B": ("B_eskistil_PIEZO002.BIN", 13.65, 17.85),
       "C": ("C_bant_PIEZO003.BIN", 10.80, 14.85), "D": ("D_bant_ve_miknatis_PIEZO004.BIN", 11.83, 15.85)}
KAN = {"A": [(0, "Eski stil, öbür uçta (X)", YES), (1, "Referans: eski stil, yanında (Y)", MAV), (2, "Mıknatıslı (Z)", TUR)],
       "B": [(0, "Eski stil, mıknatısın noktasında (X)", YES), (1, "Referans: eski stil, yanında (Y)", MAV)],
       "C": [(0, "Çift taraflı bant, mıknatısın noktasında (X)", SAR), (1, "Referans: eski stil, yanında (Y)", MAV)],
       "D": [(0, "Çift taraflı bant, öbür uçta (X)", SAR), (1, "Çift taraflı bant, yanında (Y) — artık referans değil", MAV), (2, "Mıknatıslı (Z)", TUR)]}
BAS = {"A": "Kayıt A: mıknatıslı piezo takılı", "B": "Kayıt B: mıknatısın yerine eski stil piezo",
       "C": "Kayıt C: mıknatısın yerine çift taraflı bantlı piezo",
       "D": "Kayıt D: mıknatıslı yerinde, X ve Y çift taraflı bantla (ses seviyesi az farklı olabilir)"}
fig, ax = plt.subplots(4, 1, figsize=(12, 14), sharex=True, sharey=True)
for a, (k, (ad, t0, t1)) in zip(ax, TAR.items()):
    v = oku(ad)
    i0, i1 = int(t0 * FS), int(t1 * FS)
    f = 100 + 2400 * (np.arange(i0, i1) / FS - t0) / (t1 - t0)
    for c, et, renk in sorted(KAN[k], key=lambda x: x[0] != 1):  # referans Y en arkada
        a.plot(f, v[c, i0:i1], lw=0.4, color=renk, label=et)
    a.axhline(-1900, color="#52514e", lw=0.6, ls="--"); a.axhline(2190, color="#52514e", lw=0.6, ls="--")
    a.set_title(BAS[k], loc="left"); a.set_ylabel("Sinyal (LSB)")
    h, l = a.get_legend_handles_labels()
    a.legend([plt.Line2D([], [], color=x.get_color(), lw=2) for x in h], l, loc="upper right", fontsize=9)
ax[0].text(105, 2250, "ADC sınırı (kesik çizgi)", fontsize=8, color="#52514e")
ax[3].set_xlabel("Frekans (Hz) — sweep 100 Hz'den 2500 Hz'e yaklaşık 4 s'de doğrusal çıkıyor")
fig.tight_layout(); fig.savefig(OUT / "2_ham_sinyaller_ust_uste.png", dpi=100); plt.close(fig)
print("tamam")
