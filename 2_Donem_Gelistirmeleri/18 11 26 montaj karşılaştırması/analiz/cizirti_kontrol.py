# analiz.py, 16.11 klasorundeki Piezo_KaraKutu_2026-11-16.zip icindeki analiz/ klasorunden bu klasore kopyalanmali.
# -*- coding: utf-8 -*-
# 18.11 kayitlarinda cizirti/catirti kontrolu; 16.11 kapi 0 ve kapi 1 ile kiyas. Kayitlara yazmaz.
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.signal import medfilt, welch

sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("an", Path(__file__).resolve().parent / "analiz.py")
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)
P, SAKIN, FS = an.P, an.SAKIN, an.FS
YENI = Path(__file__).resolve().parents[1] / "kayitlar"
ESKI = Path(__file__).resolve().parents[2] / "16 11 26 SPI kapısı güncellemesi" / "kayitlar"
OUT = Path(sys.argv[0]).resolve().parent
DOSYA = [("16.11 kapi0 sw", ESKI / "gate0swPIEZO001.BIN"), ("16.11 kapi1 sw", ESKI / "gate1swPIEZO003.BIN"),
         ("16.11 kapi0 100", ESKI / "gate0100hzPIEZO002.BIN"), ("16.11 kapi1 100", ESKI / "gate1100hzPIEZO004.BIN"),
         ("18.11 100 (003)", YENI / "montaj100hzPIEZO003.BIN"), ("18.11 sw (004)", YENI / "montajswPIEZO004.BIN")]

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
for ad, yol in DOSYA:
    v, _ = an.oku(yol)
    v = v.astype(float)
    nb = v.shape[1] // P
    idx = an.sessiz_bloklar(v)
    tum = list(range(1, nb))  # blok 0 haric hepsi (ton/sweep bloklari dahil)
    print(f"\n{ad}: {nb} blok, sessiz {len(idx)}")
    for c, n in enumerate("XYZ"):
        r = np.abs(v[c] - medfilt(v[c], 7))
        # tum bloklar: yazma penceresi (ilk 900) ve ayni bloktaki sakin parca (1000-1900)
        W = np.concatenate([r[k * P: k * P + 900] for k in tum])
        S = np.concatenate([r[k * P + SAKIN: k * P + SAKIN + 900] for k in tum])
        Ws = np.concatenate([r[k * P: k * P + 900] for k in idx])
        Ss = np.concatenate([r[k * P + SAKIN: k * P + SAKIN + 900] for k in idx])
        # tum kayitta tek-ornek sicrama (komsularina gore)
        d = v[c, 1:-1] - 0.5 * (v[c, :-2] + v[c, 2:])
        sic = int((np.abs(d) > 30).sum())
        f, Pq = welch(np.concatenate([v[c, k * P + SAKIN:(k + 1) * P] - v[c, k * P + SAKIN:(k + 1) * P].mean() for k in idx]), FS, nperseg=2048)
        df = f[1] - f[0]
        hf = np.sqrt(Pq[(f >= 500) & (f < 5000)].sum() * df)
        print(f"  {n}: sessiz bloklar ort|r| pencere/sakin {Ws.mean():.2f}/{Ss.mean():.2f}, >15 {int((Ws>15).sum())}/{int((Ss>15).sum())} | "
              f"tum bloklar >15 {int((W>15).sum())}/{int((S>15).sum())}, maks {W.max():.0f}/{S.max():.0f} | "
              f"tek-ornek sicrama >30: {sic} | sessiz 500-5k RMS {hf:.2f}")
        if "sw" in ad:
            prof = np.array([r[k * P: k * P + 1200] for k in idx]).mean(axis=0)
            ax[c].plot(np.arange(1200) / 10, np.convolve(prof, np.ones(10) / 10, mode="same"), lw=0.9, label=ad)
            ax[c].set_ylabel(f"{n} ort |r| (LSB)")
ax[0].legend(); ax[2].set_xlabel("blok basindan ms (SD yazmasi 0'da baslar)")
fig.tight_layout(); fig.savefig(OUT / "cizirti_profil.png", dpi=90)
