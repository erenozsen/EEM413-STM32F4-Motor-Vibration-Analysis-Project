# -*- coding: utf-8 -*-
# 26.11 saglam motor ile motor1 (rulman/bilya arizali) karsilastirmasi, Cf 2 nF, ayni montaj.
# Ozet sayilar, spektrum, ham sinyal ve zarf (envelope) spektrumu.
# Kullanim: python saglam_arizali.py <saglam klasoru> <arizali klasoru> <cikti klasoru>
import sys
from pathlib import Path
import numpy as np
from scipy.signal import welch, butter, sosfiltfilt, hilbert, find_peaks
from scipy.stats import kurtosis
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
FS = 10000
KOK = Path(__file__).resolve().parents[1]
SAG, ARZ, OUT = (Path(a) for a in sys.argv[1:4]) if len(sys.argv) > 3 else \
    (KOK / "kayitlar" / "saglam_motor", KOK / "kayitlar" / "arizali_motor1", KOK / "grafikler")
YUK = [("yüksüz", "yuksuz_"), ("yarım yük", "yarimyuk_"), ("tam yük", "tamyuk_")]
EKSEN = ["X: fan kapağı, düşey", "Y: etiket, yatay", "Z: ön kapak, eksenel (mıknatıs)"]
RS, RA = "#2ca02c", "#d62728"
NPS = 2 ** 15
ZARF_BANT = (1000, 4500)


def oku(p):
    d = np.fromfile(p, dtype="<u2")
    d = d[: len(d) // 3 * 3].reshape(-1, 3).astype(float)
    return d - np.median(d, axis=0)


def dosyalar(klasor, onek):
    return sorted(klasor.glob(onek + "*.BIN"))


def spektrum(ds):
    P = []
    for d in ds:
        f, s = welch(d, fs=FS, window="hann", nperseg=NPS, noverlap=NPS // 2, scaling="spectrum", axis=0, detrend="constant")
        P.append(s)
    return f, np.sqrt(2 * np.mean(P, axis=0))


def zarf_spektrum(ds):
    sos = butter(4, ZARF_BANT, btype="bandpass", fs=FS, output="sos")
    P = []
    for d in ds:
        e = np.abs(hilbert(sosfiltfilt(sos, d, axis=0), axis=0))
        f, s = welch(e, fs=FS, window="hann", nperseg=NPS, noverlap=NPS // 2, scaling="spectrum", axis=0, detrend="constant")
        P.append(s)
    return f, np.sqrt(2 * np.mean(P, axis=0))


def bir_x(f, A):
    m = (f > 40) & (f < 52)
    return f[m][np.argmax(A[m, 1])]


veri = {}
for ad, onek in YUK:
    for durum, kl in (("sağlam", SAG), ("arızalı", ARZ)):
        ds = [oku(p) for p in dosyalar(kl, onek)]
        veri[(ad, durum)] = ds

# ---------------- ozet tablo ----------------
print("Durum                      | RMS X/Y/Z (LSB)   | tepe faktörü X/Y/Z | basıklık (kurtosis) X/Y/Z | 1x (Hz)")
ozet = {}
for ad, _ in YUK:
    for durum in ("sağlam", "arızalı"):
        ds = veri[(ad, durum)]
        rms = np.mean([d.std(axis=0) for d in ds], axis=0)
        cf = np.mean([np.abs(d).max(axis=0) / d.std(axis=0) for d in ds], axis=0)
        ku = np.mean([kurtosis(d, axis=0, fisher=False) for d in ds], axis=0)
        f, A = spektrum(ds)
        f1 = bir_x(f, A)
        ozet[(ad, durum)] = (rms, cf, ku, f1, f, A)
        print(f"{ad:10s} {durum:8s}       | {'/'.join(f'{x:4.0f}' for x in rms)} | {'/'.join(f'{x:4.1f}' for x in cf)}     | {'/'.join(f'{x:5.1f}' for x in ku)}         | {f1:.2f}")

print("\nBant RMS (LSB) X/Y/Z: sağlam -> arızalı (oran)")
for ad, _ in YUK:
    for lo, hi in [(5, 45), (45, 520), (520, 1000), (1000, 2000), (2000, 3000), (3000, 5000)]:
        r = []
        for durum in ("sağlam", "arızalı"):
            f, A = ozet[(ad, durum)][4:6]
            m = (f >= lo) & (f < hi)
            r.append(np.sqrt(np.sum(A[m] ** 2, axis=0) / 2))
        print(f"  {ad:10s} {lo:4d}-{hi:4d} Hz: " + "  ".join(f"{e} {r[0][k]:4.0f}->{r[1][k]:4.0f} (x{r[1][k] / max(r[0][k], 1e-9):4.1f})" for k, e in enumerate("XYZ")))

print("\nHarmonikler (LSB) X/Y/Z, sağlam | arızalı")
for ad, _ in YUK:
    for h in (1, 2, 3, 4):
        s = []
        for durum in ("sağlam", "arızalı"):
            f, A = ozet[(ad, durum)][4:6]; f1 = ozet[(ad, durum)][3]
            m = (f > h * f1 - 0.8) & (f < h * f1 + 0.8)
            s.append("/".join(f"{x:.0f}" for x in A[m].max(axis=0)))
        print(f"  {ad:10s} {h}x: {s[0]:>14s} | {s[1]:>14s}")

# ---------------- zarf spektrumu tepe frekanslari ----------------
print(f"\nZarf spektrumu ({ZARF_BANT[0]}-{ZARF_BANT[1]} Hz bandı), 5-400 Hz arası en büyük tepeler (Hz, x1x, genlik)")
zarf = {}
for ad, _ in YUK:
    for durum in ("sağlam", "arızalı"):
        fz, Z = zarf_spektrum(veri[(ad, durum)])
        zarf[(ad, durum)] = (fz, Z)
        f1 = ozet[(ad, durum)][3]
        for k, e in enumerate("XYZ"):
            m = (fz > 5) & (fz < 400)
            pk, _ = find_peaks(Z[m, k], distance=max(1, int(3 / (fz[1] - fz[0]))))
            en = pk[np.argsort(Z[m, k][pk])[::-1][:5]]
            print(f"  {ad:10s} {durum:8s} {e}: " + ", ".join(f"{fz[m][i]:.1f} ({fz[m][i] / f1:.2f}x) {Z[m, k][i]:.1f}" for i in sorted(en)))

# ---------------- grafik 1: spektrum ----------------
fig, ax = plt.subplots(3, 3, figsize=(17, 10), sharex=True, sharey=True)
for j, (ad, _) in enumerate(YUK):
    for k in range(3):
        for durum, renk, lw in (("sağlam", RS, 0.8), ("arızalı", RA, 0.6)):
            f, A = ozet[(ad, durum)][4:6]
            ax[k, j].semilogy(f, A[:, k], color=renk, lw=lw, label=f"{durum} motor", alpha=0.9 if durum == "sağlam" else 0.75)
        ax[k, j].set_xlim(0, 5000); ax[k, j].set_ylim(0.05, 500); ax[k, j].grid(alpha=0.3, which="both")
        if j == 0: ax[k, j].set_ylabel(f"{EKSEN[k]}\ntepe genlik (LSB)")
    ax[0, j].set_title(ad)
    ax[2, j].set_xlabel("frekans (Hz)")
ax[0, 0].legend(loc="upper right")
fig.suptitle("Sağlam motor ve rulman/bilya arızalı motor (motor1): genlik spektrumu, 26.11.2026, Cf = 2 nF, aynı montaj")
fig.tight_layout(); fig.savefig(OUT / "saglam_arizali_spektrum.png", dpi=120); plt.close(fig)

# ---------------- grafik 2: ham sinyal ----------------
fig, ax = plt.subplots(3, 1, figsize=(13, 8.5), sharex=True)
t = np.arange(int(0.2 * FS)) / FS * 1000
for k in range(3):
    for durum, renk in (("arızalı", RA), ("sağlam", RS)):
        d = veri[("tam yük", durum)][0]
        bas = int(2 * FS)
        ax[k].plot(t, d[bas:bas + len(t), k] + 1900, color=renk, lw=0.8, label=f"{durum} motor")
    ax[k].axhline(4095, color="k", ls="--", lw=0.7); ax[k].axhline(0, color="k", ls="--", lw=0.7)
    ax[k].set_ylim(-100, 4200); ax[k].set_ylabel(f"{EKSEN[k]}\nADC kodu")
ax[0].legend(loc="upper right"); ax[2].set_xlabel("zaman (ms)")
fig.suptitle("Tam yükte 200 ms ham sinyal: sağlam ve arızalı motor üst üste (kesikli çizgiler ADC sınırları)")
fig.tight_layout(); fig.savefig(OUT / "saglam_arizali_ham_sinyal.png", dpi=120); plt.close(fig)

# ---------------- grafik 3: zarf spektrumu ----------------
fig, ax = plt.subplots(3, 3, figsize=(17, 10), sharex=True)
for j, (ad, _) in enumerate(YUK):
    f1a = ozet[(ad, "arızalı")][3]
    for k in range(3):
        for durum, renk in (("sağlam", RS), ("arızalı", RA)):
            fz, Z = zarf[(ad, durum)]
            ax[k, j].plot(fz, Z[:, k], color=renk, lw=0.9, label=f"{durum} motor")
        for h in range(1, 9):
            ax[k, j].axvline(h * f1a, color="gray", lw=0.5, ls=":")
        ax[k, j].axvline(5.40 * f1a, color="purple", lw=1.0, ls="--", alpha=0.6)
        ax[k, j].text(5.40 * f1a + 3, 0.97, "5,40×", color="purple", fontsize=8, va="top",
                      transform=ax[k, j].get_xaxis_transform())
        ax[k, j].set_xlim(0, 400); ax[k, j].set_ylim(bottom=0); ax[k, j].grid(alpha=0.3)
        if j == 0: ax[k, j].set_ylabel(f"{EKSEN[k]}\nzarf genliği (LSB)")
    ax[0, j].set_title(f"{ad}, 1× = {f1a:.1f} Hz (gri: 1×, 2×, …)")
    ax[2, j].set_xlabel("frekans (Hz)")
ax[0, 0].legend(loc="upper right")
fig.suptitle(f"Zarf (envelope) spektrumu: {ZARF_BANT[0]}–{ZARF_BANT[1]} Hz bandındaki darbelerin tekrarlanma frekansı")
fig.tight_layout(); fig.savefig(OUT / "saglam_arizali_zarf_spektrumu.png", dpi=120); plt.close(fig)
print("\ngrafikler:", OUT)
