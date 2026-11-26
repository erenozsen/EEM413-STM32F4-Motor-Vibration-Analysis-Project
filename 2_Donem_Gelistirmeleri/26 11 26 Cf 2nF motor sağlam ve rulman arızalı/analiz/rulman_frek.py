import sys
from pathlib import Path
import numpy as np
from scipy.signal import welch, butter, sosfiltfilt, hilbert
sys.stdout.reconfigure(encoding="utf-8")
FS=10000; NPS=2**15
A=Path(__file__).resolve().parents[1]/"kayitlar"
sos=butter(4,(1000,4500),btype="bandpass",fs=FS,output="sos")
def zarf(pat,kl):
    P=[]
    for p in sorted((A/kl).glob(pat)):
        d=np.fromfile(p,dtype="<u2"); d=d[:len(d)//3*3].reshape(-1,3).astype(float); d-=np.median(d,axis=0)
        e=np.abs(hilbert(sosfiltfilt(sos,d,axis=0),axis=0))
        f,s=welch(e,fs=FS,nperseg=NPS,noverlap=NPS//2,scaling="spectrum",axis=0); P.append(s)
    return f,np.sqrt(2*np.mean(P,axis=0))
r=0.2015
oran={"FTF 0,40":0.5*(1-r),"BSF 2,40":(1/(2*r))*(1-r*r),"BPFO 3,59":4.5*(1-r),"2xBSF 4,76":(1/r)*(1-r*r),"BPFI 5,41":4.5*(1+r),"BPFI-1x 4,41":4.5*(1+r)-1,"BPFI+1x 6,41":4.5*(1+r)+1}
for ad,pat,f1 in [("yuksuz","yuksuz_*.BIN",49.44),("yarimyuk","yarimyuk_*.BIN",48.22),("tamyuk","tamyuk_*.BIN",46.69)]:
    fs,Zs=zarf(pat,"saglam_motor"); fa,Za=zarf(pat,"arizali_motor1")
    print(f"\n{ad} (1x={f1} Hz)   saglam X/Y/Z | arizali X/Y/Z  (taban: arizali medyan 5-400 Hz)")
    m=(fa>5)&(fa<400); taban=np.median(Za[m],axis=0)
    print("   taban arizali:", "/".join(f"{x:.1f}" for x in taban))
    for k,v in oran.items():
        f0=v*f1; ms=(fs>f0-0.8)&(fs<f0+0.8)
        print(f"   {k:13s} {f0:6.1f} Hz: " + "/".join(f"{x:5.1f}" for x in Zs[ms].max(axis=0)) + " | " + "/".join(f"{x:5.1f}" for x in Za[ms].max(axis=0)))
