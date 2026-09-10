"""Normaliza a saida do transcribe -> palavras e frases com tempo.
Video sem fala volta com no_speech=True em vez de estourar."""
import json, re
from config import PAUSA_MIN

def _sec(s):
    return float(str(s).rstrip("s")) if s is not None else None

def load(path):
    d = json.load(open(path))
    steps = d.get("steps") or []
    if not steps or not steps[0].get("content"):
        return dict(text="", words=[], sents=[], dur=0.0, no_speech=True,
                    tokens=d.get("usage", {}).get("total_tokens"))
    step = steps[0]["content"][0]
    words = [dict(w=a["text"], start=_sec(a.get("start_offset")), end=_sec(a.get("end_offset")))
             for a in step.get("annotations", []) if a.get("type") == "word_info"]
    sents, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?]$", w["w"].strip()):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    out = [dict(text=" ".join(x["w"] for x in g).strip(), start=g[0]["start"], end=g[-1]["end"])
           for g in sents if g]
    return dict(text=step["text"], words=words, sents=out, no_speech=False,
                dur=words[-1]["end"] if words else 0.0,
                tokens=d.get("usage", {}).get("total_tokens"))

def gaps(words, min_gap=PAUSA_MIN):
    return [(a["end"], b["start"]) for a, b in zip(words, words[1:])
            if (b["start"] or 0) - (a["end"] or 0) >= min_gap]
