# -*- coding: utf-8 -*-
# Motor kayitlarinin hizli ozeti: sure, bitis, kirpilma, 1x frekans ve harmonik genlikleri, saniyelik RMS
import sys
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
FS = 10000
BLOK = 24576


def oku(p):
    d = np.fromfile(p, dtype="<u2")
    d = d[: len(d) // 3 * 3].reshape(-1, 3).astype(float)
    return d


def tepe(x, f0, gen=1.5):
    n = len(x)
    w = np.hanning(n)
    X = np.abs(np.fft.rfft((x - x.mean()) * w)) * 2 / w.sum()
    f = np.fft.rfftfreq(n, 1 / FS)
    m = (f > f0 - gen) & (f < f0 + gen)
    i = np.argmax(X[m])
    return f[m][i], X[m][i]


for ad in sys.argv[1:]:
    p = Path(ad)
    b = p.stat().st_size
    if b < 6:
        print(f"\n### {p.name}: {b} bayt, bos")
        continue
    d = oku(p)
    n = len(d)
    bitis = "TAM BLOK KATI (anormal)" if b % BLOK == 0 else "butonla"
    print(f"\n### {p.name}: {b} B, {n / FS:.2f} s, {bitis}")
    for k, ad_k in enumerate("XYZ"):
        x = d[:, k]
        kir = int(np.sum((x >= 4095) | (x <= 0)))
        print(f"  {ad_k}: medyan {np.median(x):.0f}, std {x.std():.0f}, kirpik {kir}")
    # saniyelik RMS (Y), motor ne zaman calisiyor
    s = int(n // FS)
    rms = [d[i * FS:(i + 1) * FS].std(axis=0) for i in range(s)]
    print("  sn RMS X/Y/Z:", " | ".join(f"{r[0]:.0f}/{r[1]:.0f}/{r[2]:.0f}" for r in rms))
    # en kararli bolum: ortadaki parca (motor calisiyorsa)
    seg = d[n // 4: 3 * n // 4] if n > 4 * FS else d
    # 1x: Y kanalinda 40-52 Hz en buyuk tepe
    f1, _ = tepe(seg[:, 1], 46, 6)
    satir = f"  1x = {f1:.2f} Hz ({f1 * 60:.0f} rpm)  genlik (LSB tepe) 1x/2x/3x/4x:"
    for k, ad_k in enumerate("XYZ"):
        g = [tepe(seg[:, k], h * f1, 1.0)[1] for h in (1, 2, 3, 4)]
        satir += f"  {ad_k} " + "/".join(f"{v:.0f}" for v in g)
    print(satir)
    _, a100 = tepe(seg[:, 1], 100.0, 0.3)
    print(f"  Y 100.0 Hz: {a100:.0f}")
