# -*- coding: utf-8 -*-
# 26.11 motor (Cf 2 nF): yuksuz / yarim yuk / tam yuk genlik spektrumu. Her durumun iki tekrari
# birlikte ortalanir (Welch, 2^15 ornek = 3,3 s pencere, ~0,3 Hz cozunurluk).
# Kullanim: python spektrum_yuk.py <kayit klasoru> <cikti klasoru>
import sys
from pathlib import Path
import numpy as np
from scipy.signal import welch, find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
FS = 10000
KOK = Path(__file__).resolve().parents[1]
KAY = Path(sys.argv[1]) if len(sys.argv) > 1 else KOK / "kayitlar" / "saglam_motor"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else KOK / "grafikler"
DURUM = [("yüksüz", "yuksuz_*Cf2nF_*.BIN", "#2ca02c"),
         ("yarım yük", "yarimyuk_*Cf2nF_*.BIN", "#ff7f0e"),
         ("tam yük", "tamyuk_*Cf2nF_*.BIN", "#d62728")]
EKSEN = ["X (PA3)", "Y (PA1)", "Z (PA2)"]
NPS = 2 ** 15


def genlik_spektrumu(desen):
    """Iki tekrarin ortalama genlik spektrumu (sinus tepe genligi, LSB)."""
    P = []
    for p in sorted(KAY.glob(desen)):
        d = np.fromfile(p, dtype="<u2"); d = d[: len(d) // 3 * 3].reshape(-1, 3).astype(float)
        f, s = welch(d - d.mean(axis=0), fs=FS, window="hann", nperseg=NPS, noverlap=NPS // 2,
                     scaling="spectrum", axis=0, detrend=False)
        P.append(s)
    return f, np.sqrt(2 * np.mean(P, axis=0))   # (frekans, eksen)


sonuc = {ad: genlik_spektrumu(desen) for ad, desen, _ in DURUM}
f = sonuc["yüksüz"][0]

# 1x: Y'de 40-52 Hz arasindaki en buyuk tepe
bir_x = {}
for ad, (ff, A) in sonuc.items():
    m = (ff > 40) & (ff < 52)
    bir_x[ad] = ff[m][np.argmax(A[m, 1])]

# ---------------- tablo ----------------
def tepe(A, ff, f0, gen=0.8):
    m = (ff > f0 - gen) & (ff < f0 + gen)
    return A[m].max(axis=0) if m.any() else np.zeros(3)

print("1x frekansi:", {k: round(v, 2) for k, v in bir_x.items()})
print("\nTepe genlikler (LSB), X / Y / Z")
print(f"{'':14s}" + "".join(f"{ad:>22s}" for ad, _, _ in DURUM))
for ad_h, h in [("1x", 1), ("2x", 2), ("3x", 3), ("4x", 4), ("5x", 5), ("6x", 6)]:
    satir = f"{ad_h:14s}"
    for ad, _, _ in DURUM:
        ff, A = sonuc[ad]; v = tepe(A, ff, h * bir_x[ad])
        satir += f"{'/'.join(f'{x:.0f}' for x in v):>22s}"
    print(satir)
for ad_h, f0 in [("100 Hz (şebeke)", 100.0)]:
    satir = f"{ad_h:14s}"
    for ad, _, _ in DURUM:
        ff, A = sonuc[ad]; v = tepe(A, ff, f0, 0.25)
        satir += f"{'/'.join(f'{x:.0f}' for x in v):>22s}"
    print(satir)
print("\nBant RMS (LSB), X / Y / Z")
for lo, hi in [(5, 45), (45, 520), (520, 2000), (2000, 5000)]:
    satir = f"{lo}-{hi} Hz".ljust(14)
    for ad, _, _ in DURUM:
        ff, A = sonuc[ad]; m = (ff >= lo) & (ff < hi)
        satir += f"{'/'.join(f'{x:.0f}' for x in np.sqrt(np.sum(A[m] ** 2, axis=0) / 2)):>22s}"
    print(satir)
print("\nYuksek frekansta en buyuk 4 tepe (>500 Hz), Hz/LSB")
for ad, _, _ in DURUM:
    ff, A = sonuc[ad]
    for k, e in enumerate("XYZ"):
        m = ff > 500
        pk, _ = find_peaks(A[m, k], distance=int(20 / (ff[1] - ff[0])))
        en = pk[np.argsort(A[m, k][pk])[::-1][:4]]
        print(f"  {ad:10s} {e}: " + ", ".join(f"{ff[m][i]:.0f}/{A[m, k][i]:.0f}" for i in sorted(en)))

# ---------------- grafik ----------------
fig, ax = plt.subplots(3, 2, figsize=(15, 10), gridspec_kw={"width_ratios": [1.1, 1]})
for k in range(3):
    for ad, _, renk in DURUM:
        ff, A = sonuc[ad]
        ax[k, 0].plot(ff, A[:, k], color=renk, lw=1, label=f"{ad} (1× = {bir_x[ad]:.1f} Hz)")
        ax[k, 1].semilogy(ff, A[:, k], color=renk, lw=0.7, label=ad)
    for h in range(1, 6):
        for ad, _, renk in DURUM:
            ax[k, 0].axvline(h * bir_x[ad], color=renk, lw=0.5, ls=":", alpha=0.7)
        ax[k, 0].text(h * bir_x["yüksüz"], 1.0, f"{h}×", transform=ax[k, 0].get_xaxis_transform(),
                      ha="center", va="bottom", fontsize=8)
    ax[k, 0].set_xlim(0, 270); ax[k, 0].set_ylim(bottom=0)
    ax[k, 0].set_ylabel(f"{EKSEN[k]}\ntepe genlik (LSB)")
    ax[k, 1].set_xlim(0, 5000); ax[k, 1].set_ylim(0.05, 300)
    ax[k, 0].grid(alpha=0.3); ax[k, 1].grid(alpha=0.3, which="both")
ax[0, 0].legend(loc="upper right", fontsize=8)
ax[0, 1].legend(loc="upper right", fontsize=8)
ax[0, 0].set_title("0–270 Hz: dönüş frekansı (1×) ve harmonikleri")
ax[0, 1].set_title("0–5000 Hz: tüm bant (log ölçek)")
ax[2, 0].set_xlabel("frekans (Hz)"); ax[2, 1].set_xlabel("frekans (Hz)")
fig.suptitle("Motor titreşim spektrumu, 26.11.2026, Cf = 2 nF (her durumun iki tekrarının ortalaması)")
fig.tight_layout()
fig.savefig(OUT / "spektrum_yuksuz_yarim_tam.png", dpi=130)
print("\nkaydedildi:", OUT / "spektrum_yuksuz_yarim_tam.png")
