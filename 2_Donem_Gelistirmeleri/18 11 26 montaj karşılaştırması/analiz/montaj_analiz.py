# analiz.py, 16.11 klasorundeki Piezo_KaraKutu_2026-11-16.zip icindeki analiz/ klasorunden bu klasore kopyalanmali.
# -*- coding: utf-8 -*-
# Montaj karsilastirmasi (18.11): yeni kayitlari 16.11 kapi 1 kayitlariyla kiyaslar. Kayitlara yazmaz.
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.signal import welch, stft

sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("an", Path(__file__).resolve().parent / "analiz.py")
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)
FS = an.FS
YENI = Path(__file__).resolve().parents[1] / "kayitlar"
ESKI = Path(__file__).resolve().parents[2] / "16 11 26 SPI kapısı güncellemesi" / "kayitlar"
CIZ = Path(sys.argv[0]).resolve().parent
DOSYA = {"yeni_003": YENI / "montaj100hzPIEZO003.BIN", "yeni_004": YENI / "montajswPIEZO004.BIN",
         "1611_sw003": ESKI / "gate1swPIEZO003.BIN", "1611_100hz004": ESKI / "gate1100hzPIEZO004.BIN"}

veri = {}
for ad, yol in DOSYA.items():
    v, _ = an.oku(yol)
    v = v.astype(float)
    v -= np.median(v, axis=1, keepdims=True)
    veri[ad] = v

# 1) Saniye basina baskin frekans (Y kanali) -> hangi kayit sweep, hangisi ton
for ad, v in veri.items():
    f, t, Z = stft(v[1], FS, nperseg=FS, noverlap=0)
    A = np.abs(Z)
    A[f < 15] = 0
    bas = [f"{f[A[:, i].argmax()]:.0f}" if A[:, i].max() > 5 * np.median(A[:, i]) else "-" for i in range(A.shape[1])]
    print(f"{ad:14s} Y baskin Hz/s: {' '.join(bas)}")
    print(f"{'':14s} DC orta (ham): ", end="")
    w, _ = an.oku(DOSYA[ad])
    print(" ".join(f"{np.median(w[c]):.0f}" for c in range(3)))


def aktif(v, esik=4.0):
    s = np.array([v[1, i:i + FS // 4].std() for i in range(0, v.shape[1] - FS // 4 + 1, FS // 4)])
    ak = np.nonzero(s > esik * np.median(s))[0]
    return ak.min() * FS // 4 + FS // 2, (ak.max() + 1) * FS // 4 - FS // 2


# 2) Ton kayitlari: temel ve harmonikler (kanal basina, LSB tepe)
def harmonik(v):
    a, b = aktif(v)
    out = []
    for c in range(3):
        x = v[c, a:b]
        x = x - x.mean()
        n = len(x)
        win = np.hanning(n)
        X = np.abs(np.fft.rfft(x * win)) * 2 / win.sum()
        fr = np.fft.rfftfreq(n, 1 / FS)
        f0 = fr[np.argmax(np.where((fr > 40) & (fr < 2000), X, 0))]
        h = []
        for k in range(1, 6):
            m = (fr > k * f0 - 2) & (fr < k * f0 + 2)
            h.append(X[m].max())
        out.append((f0, h))
    return (a / FS, b / FS), out


for ad in ("yeni_004", "yeni_003", "1611_100hz004", "1611_sw003"):
    (ta, tb), out = harmonik(veri[ad])
    print(f"\n{ad}: aktif {ta:.1f}-{tb:.1f} s")
    for n, (f0, h) in zip("XYZ", out):
        thd = np.sqrt(sum(x * x for x in h[1:])) / h[0] * 100
        print(f"  {n}: f0 {f0:.2f} Hz, harmonikler(LSB) " + " ".join(f"{x:.2f}" for x in h) + f" | THD {thd:.2f} %")

# 3) Genis bant spektrum orani (aktif bolum PSD - sessiz PSD), kanallar arasi
def psd_aktif(v):
    a, b = aktif(v)
    f, P = welch(v[:, a:b], FS, nperseg=4096, axis=1)
    _, Q = welch(v[:, FS // 2: FS * 7], FS, nperseg=4096, axis=1)
    return f, P, Q


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(2, 2, figsize=(14, 9))
bantlar = [(20, 60), (60, 150), (150, 400), (400, 1000), (1000, 2000), (2000, 4000)]
for j, ad in enumerate(("yeni_003", "yeni_004", "1611_sw003", "1611_100hz004")):
    f, P, Q = psd_aktif(veri[ad])
    sn = P / Q
    print(f"\n{ad}: bant RMS (aktif, LSB) ve SNR")
    for lo, hi in bantlar:
        m = (f >= lo) & (f < hi)
        df = f[1] - f[0]
        r = [np.sqrt(P[c, m].sum() * df) for c in range(3)]
        q = [np.sqrt(Q[c, m].sum() * df) for c in range(3)]
        print(f"  {lo:5d}-{hi:5d} Hz  X {r[0]:7.1f}  Y {r[1]:7.1f}  Z {r[2]:7.1f}  | sessiz X {q[0]:.2f} Y {q[1]:.2f} Z {q[2]:.2f} | Z/Y {r[2]/r[1]:.3f} X/Y {r[0]/r[1]:.3f}")
    if j < 4:
        a = ax.flat[j]
        for c, n in enumerate("XYZ"):
            a.semilogy(f, P[c], lw=0.7, label=n)
        a.semilogy(f, Q[2], lw=0.5, color="gray", label="Z sessiz")
        a.set_xlim(0, 3000); a.set_title(ad); a.legend(); a.set_xlabel("Hz")
fig.tight_layout(); fig.savefig(CIZ / "montaj_psd.png", dpi=80); plt.close(fig)

# 4) Sweep: kanallar arasi oran egrisi (dB), yeni ve 16.11
fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
for ad, st in (("1611_sw003", "--"), ("yeni_003", "-"), ("yeni_004", ":")):
    f, P, Q = psd_aktif(veri[ad])
    k = np.convolve(np.ones(9) / 9, np.ones(1), mode="full")
    sm = lambda y: np.convolve(y, np.ones(9) / 9, mode="same")
    ax[0].plot(f, 10 * np.log10(sm(P[2]) / sm(P[1])), st, label=f"{ad} Z/Y")
    ax[1].plot(f, 10 * np.log10(sm(P[0]) / sm(P[1])), st, label=f"{ad} X/Y")
for a in ax:
    a.set_xlim(20, 3000); a.set_ylim(-40, 15); a.grid(True); a.legend(); a.set_ylabel("dB")
ax[1].set_xlabel("Hz")
fig.tight_layout(); fig.savefig(CIZ / "montaj_oran.png", dpi=80); plt.close(fig)
