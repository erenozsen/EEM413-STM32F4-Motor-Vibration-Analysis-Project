# -*- coding: utf-8 -*-
# 26.11 hoparlor 100-5000 Hz sweep (Cf 2 nF) hizli ozet
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
FS = 10000
for p in sys.argv[1:]:
    d = np.fromfile(p, dtype="<u2"); d = d[:len(d)//3*3].reshape(-1, 3).astype(float)
    n = len(d)
    print(f"\n### {p.split(chr(92))[-1]}: {n/FS:.2f} s")
    for k, a in enumerate("XYZ"):
        x = d[:, k]
        print(f"  {a}: medyan {np.median(x):.0f} min {x.min():.0f} max {x.max():.0f} "
              f"kirpik {int(np.sum((x>=4095)|(x<=0)))} std {x.std():.0f}")
    # 0,5 s pencerelerde: baskin frekans (en buyuk kanaldan) ve her kanalin tepe sapmasi
    W = FS // 2
    print("   t(s)  f(Hz)   X tepe  Y tepe  Z tepe   (tepe = max|x-medyan|, LSB)")
    med = np.median(d[:int(2*FS)], axis=0)
    for i in range(n // W):
        s = d[i*W:(i+1)*W]
        ac = s - s.mean(axis=0)
        k = np.argmax(ac.std(axis=0))
        X = np.abs(np.fft.rfft(ac[:, k] * np.hanning(W)))
        f = np.fft.rfftfreq(W, 1/FS)
        f0 = f[np.argmax(X[5:]) + 5]
        tp = np.max(np.abs(s - med), axis=0)
        print(f"  {i*0.5:5.1f} {f0:6.0f}  " + "  ".join(f"{v:6.0f}" for v in tp))
