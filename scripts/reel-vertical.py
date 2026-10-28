import cv2, numpy as np, subprocess, sys
FF = r"C:/Users/dmp20/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
CL = r"C:/Users/dmp20/Lou López/design/clips/"
# Lou's centre, % of frame width, read off the gridded frame sheets
K = {
 "03-final-triple-ala": [(0,5),(1,8),(2,17),(3,18),(4,21),(4.4,29),(4.6,30),(4.8,36),(5.5,48),(6.5,40),(7,43),(7.5,46),(8.1,46)],
 "05-avenida-entrada": [(0,46),(1,43),(2,29),(3,41),(4,46),(4.5,40),(5,30),(6.1,30)],
 "02-final-triple-transicion": [(0,13),(1,16),(2,16),(2.5,18),(3,15),(3.5,18),(4.5,13),(4.9,50),(5,57),(6,73),(7,75),(8.1,75)],
 "10-uconn-sweet16-triple": [(0,12),(1,15),(2,20),(3,12),(4,25),(5,28),(6,22),(7,20),(8.6,25)],
 "07-avenida-triple": [(0,52),(1,52),(1.5,45),(2.1,45),(2.2,72),(2.5,72),(3,52),(3.5,47),(4,40),(4.5,62),(5,45),(5.6,37)],
 "09-avenida-entrada-falta": [(0,50),(1.7,52),(1.76,58),(2,60),(3,85),(3.5,80),(4,65),(5,30),(6,50),(6.6,50)],
}
OW, OH = 720, 1280
for c, kf in K.items():
    if len(sys.argv) > 1 and c not in sys.argv[1:]: continue
    cap = cv2.VideoCapture(CL + c + ".mp4"); fps = cap.get(5); n = int(cap.get(7))
    t = np.arange(n) / fps
    x = np.interp(t, [a for a, b in kf], [b for a, b in kf])
    s = max(1, int(0.12 * fps)); k = np.exp(-0.5 * (np.arange(-3*s, 3*s+1) / s) ** 2); k /= k.sum()
    x = np.convolve(np.pad(x, 3*s, mode="edge"), k, mode="valid")
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", f"v-{c}.mp4"], stdin=subprocess.PIPE)
    for i in range(n):
        ok, f = cap.read()
        if not ok: break
        if f.shape[1] != 1920: f = cv2.resize(f, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)
        cw = round(1080 * 9 / 16)
        cx = min(max(x[i] / 100 * 1920, cw / 2), 1920 - cw / 2)
        x0 = int(round(cx - cw / 2))
        p.stdin.write(cv2.resize(f[:, x0:x0+cw], (OW, OH), interpolation=cv2.INTER_LANCZOS4).tobytes())
    p.stdin.close(); p.wait(); print(c, n, flush=True)
