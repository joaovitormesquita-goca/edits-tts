"""Executa o corte. Escopo: SO corte -- nada de TTS, hook novo ou legenda.

Duas coisas fazem a emenda soar bem:
1. snap: o ponto de corte migra pro meio da pausa mais proxima, entao nunca
   cai no ataque ou na cauda de uma palavra;
2. fade de 20ms em cada ponta de segmento, que elimina o estalo da emenda.
Video e' corte seco: o material e' B-roll de produto sem rosto falando, e nesse
contexto jump cut le como edicao normal.
"""
import os, subprocess
import norm
from config import MIN_SEG, MIN_OUT, SNAP_TOL, FADE, PAD

def merge(spans):
    out = []
    for s, e in sorted(spans):
        if s is None or e is None or e <= s:
            continue
        if out and s <= out[-1][1] + 0.01:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out

def snap(t, gaps, tol=SNAP_TOL):
    best = None
    for a, b in gaps:
        mid = (a + b) / 2
        d = abs(mid - t)
        if d <= tol and (best is None or d < best[0]):
            best = (d, mid)
    return best[1] if best else t

def plan(tx_path, remover, dur):
    """-> (segmentos_mantidos, trechos_removidos)"""
    d = norm.load(tx_path)
    g = norm.gaps(d["words"])
    rem = []
    for s, e in merge([[r.get("start"), r.get("end")] for r in (remover or [])]):
        s2 = 0.0 if s <= 0.35 else snap(s - PAD, g)
        e2 = dur if e >= dur - 0.35 else snap(e + PAD, g)
        rem.append([max(0.0, s2), min(dur, e2)])
    rem = merge(rem)
    keep, cur = [], 0.0
    for s, e in rem:
        if s - cur >= MIN_SEG:
            keep.append([round(cur, 3), round(s, 3)])
        cur = max(cur, e)
    if dur - cur >= MIN_SEG:
        keep.append([round(cur, 3), round(dur, 3)])
    return keep, rem

def render(src, keep, dst):
    parts, maps = [], []
    for i, (s, e) in enumerate(keep):
        L = e - s
        f = min(FADE, L / 4)
        parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:st=0:d={f:.3f},afade=t=out:st={max(0, L - f):.3f}:d={f:.3f}[a{i}]")
        maps.append(f"[v{i}][a{i}]")
    fc = ";".join(parts) + ";" + "".join(maps) + f"concat=n={len(keep)}:v=1:a=1[v][a]"
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src,
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst],
        capture_output=True, text=True)
    return r.returncode, r.stderr[-400:]

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0
