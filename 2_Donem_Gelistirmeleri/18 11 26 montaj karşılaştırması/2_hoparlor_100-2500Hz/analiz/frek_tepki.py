# -*- coding: utf-8 -*-
# 18.11 aksam: 100-2500 Hz sweep, montaj yontemlerinin frekans tepkisi. Kayitlara yazmaz.
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parents[1] / "kayitlar"
AD = {"A": "A_miknatisli_PIEZO001.BIN", "B": "B_eskistil_PIEZO002.BIN", "C": "C_bant_PIEZO003.BIN", "D": "D_bant_ve_miknatis_PIEZO004.BIN"}
FS = 10000
N = 200          # 20 ms cerceve
KUTU = np.arange(100, 2551, 50)


def oku(y):
    d = np.fromfile(y, dtype=np.uint16)
    return d[: len(d) // 3 * 3].reshape(-1, 3).T.astype(float)


def cerceveler(ham):
    """Her cerceve: frekans (Y'nin sifir gecislerinden), kanal genlikleri (RMS*sqrt2), kirpilma bayragi."""
    v = ham - np.median(ham, axis=1, keepdims=True)
    sessiz = np.median([v[1, i:i + N].std() for i in range(0, 50000, N)])
    fr, amp, kir = [], [], []
    for i in range(0, v.shape[1] - N, N):
        s = v[:, i:i + N] - v[:, i:i + N].mean(axis=1, keepdims=True)
        if s[1].std() < 8 * sessiz:
            continue
        y = s[1]
        z = np.nonzero((y[:-1] < 0) & (y[1:] >= 0))[0]
        if len(z) < 3:
            continue
        tz = z + (-y[z]) / (y[z + 1] - y[z])
        fr.append((len(tz) - 1) / (tz[-1] - tz[0]) * FS)
        amp.append(s.std(axis=1) * np.sqrt(2))
        h = ham[:, i:i + N]
        kir.append(((h <= 3) | (h >= 4092)).any(axis=1))
    return np.array(fr), np.array(amp), np.array(kir)


def kutula(fr, deger, gecerli):
    out = np.full(len(KUTU) - 1, np.nan)
    for i in range(len(KUTU) - 1):
        m = gecerli & (fr >= KUTU[i]) & (fr < KUTU[i + 1])
        if m.sum() >= 2:
            out[i] = np.median(deger[m])
    return out


FK = (KUTU[:-1] + KUTU[1:]) / 2
S = {}
for k, ad in AD.items():
    fr, amp, kir = cerceveler(oku(KOK / ad))
    S[k] = dict(fr=fr, amp=amp, kir=kir)
    print(f"{k} {ad}: {len(fr)} sinyalli cerceve, kirpilmis cerceve X {kir[:,0].sum()} Y {kir[:,1].sum()} Z {kir[:,2].sum()}")
    for c, n in enumerate("XYZ"):
        kf = fr[kir[:, c]]
        if len(kf):
            h, _ = np.histogram(kf, KUTU)
            bas = [f"{int(KUTU[i])}" for i in np.nonzero(h)[0]]
            print(f"   {n} kirpilan frekans kutulari: {' '.join(bas)}")


def oran(k, c):
    s = S[k]
    g = ~s["kir"][:, c] & ~s["kir"][:, 1]
    return kutula(s["fr"], s["amp"][:, c] / s["amp"][:, 1], g)


def genlik(k, c):
    s = S[k]
    return kutula(s["fr"], s["amp"][:, c], ~s["kir"][:, c])


R = {"ZY_A": oran("A", 2), "XY_A": oran("A", 0), "XY_B": oran("B", 0), "XY_C": oran("C", 0),
     "ZY_D": oran("D", 2), "XY_D": oran("D", 0)}
G = {f"{n}_{k}": genlik(k, c) for k in AD for c, n in enumerate("XYZ")}
M = R["ZY_A"] / R["XY_B"]     # miknatis / eski stil (ayni nokta, farkli piezo+kanal)
T = R["XY_C"] / R["XY_B"]     # bant / eski stil (ayni nokta, ayni piezo+kanal)
TY = R["ZY_A"] / R["ZY_D"]    # Y'de bant / eski stil (Z ayni kaldiysa)

print("\n f(Hz)   Y_A   Y_B   Y_C   Y_D |  Z/Y_A  X/Y_B  X/Y_C  Z/Y_D | mikn/eski  bant/eski  Ybant/eski")
for i, f in enumerate(FK):
    print(f"{f:5.0f} " + " ".join(f"{G[f'Y_{k}'][i]:5.0f}" for k in "ABCD") + " | " +
          " ".join(f"{R[x][i]:6.3f}" for x in ("ZY_A", "XY_B", "XY_C", "ZY_D")) +
          f" | {M[i]:8.3f} {T[i]:9.3f} {TY[i]:10.3f}")
np.savez(Path(sys.argv[0]).resolve().parent / "frek_tepki.npz", FK=FK, M=M, T=T, TY=TY, **R, **G)
