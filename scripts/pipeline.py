#!/usr/bin/env python3
"""Um comando: pasta de videos crus -> videos cortados + relatorio.

  python scripts/pipeline.py <pasta_de_entrada> [--out <pasta_saida>] [--jobs 4]

Reaproveita trabalho: audio, transcricao e classificacao ficam em cache dentro de
<saida>/_trabalho, entao rodar de novo na mesma pasta so processa o que e' novo.
"""
import os, sys, json, glob, argparse, subprocess, shutil, time
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import norm, cut as cutmod
from gem_asr import transcribe
from classify import classify
from config import MIN_OUT

APROVEITA = ("TRIM", "CORTE_MIOLO")     # levam corte
PASSA     = ("LIMPO",)                  # copia direto
DESCARTA  = ("RENARRAR", "SEM_FALA")    # fora do escopo: corte nao resolve

def _proc(t):
    """Avisos e regras valem pra qualquer desfecho, nao so pra quem foi cortado:
    um descarte causado por regra local precisa dizer isso em algum lugar."""
    return dict(avisos=[x for x in (t.get("avisos") or []) if str(x).strip()],
                regras=t.get("regras_aplicadas") or [])

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def extrai_audio(src, dst):
    if os.path.exists(dst):
        return True
    r = sh(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vn",
            "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-q:a", "5", dst])
    return r.returncode == 0

def etapa(nome, itens, fn, jobs):
    print(f"\n>> {nome} ({len(itens)})", flush=True)
    res = []
    with cf.ThreadPoolExecutor(jobs) as ex:
        for i, r in enumerate(ex.map(fn, itens), 1):
            res.append(r)
            if r and r.get("msg"):
                print(f"   [{i}/{len(itens)}] {r['msg']}", flush=True)
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--out", default=None)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--regras", default=None,
                    help="arquivo .md com regras extras so pra esta rodada")
    a = ap.parse_args()

    ent = os.path.abspath(a.entrada)
    out = os.path.abspath(a.out or os.path.join(ent, "..", "cortados"))
    W = os.path.join(out, "_trabalho")
    for d in (out, W, f"{W}/audio", f"{W}/tx", f"{W}/cls"):
        os.makedirs(d, exist_ok=True)

    videos = sorted(glob.glob(os.path.join(ent, "**", "*.mp4"), recursive=True))
    videos = [v for v in videos if os.path.abspath(v) != out and "_trabalho" not in v
              and os.path.abspath(os.path.dirname(v)) != out]
    if not videos:
        raise SystemExit(f"nenhum .mp4 encontrado em {ent}")
    print(f"entrada: {ent}\nsaida:   {out}\nvideos:  {len(videos)}")
    from config import carrega_regras
    camadas = carrega_regras(ent, a.regras)
    if camadas:
        print("regras locais em uso (somam a regra base, nao afrouxam preco/plataforma):")
        for rotulo, caminho, _ in camadas:
            print(f"  - {rotulo}: {caminho}")
    else:
        print("regras locais: nenhuma (so a regra base)")

    nomes = {os.path.splitext(os.path.basename(v))[0]: v for v in videos}

    # 1. audio
    def _a(n):
        ok = extrai_audio(nomes[n], f"{W}/audio/{n}.mp3")
        return dict(name=n, ok=ok, msg=None if ok else f"FALHA audio {n}")
    etapa("extraindo audio", list(nomes), _a, a.jobs)

    # 2. transcricao
    def _t(n):
        p = f"{W}/tx/{n}.json"
        if os.path.exists(p):
            return dict(name=n, msg=None)
        try:
            json.dump(transcribe(f"{W}/audio/{n}.mp3"), open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return dict(name=n, msg=f"ok {n[:40]}")
        except Exception as e:
            return dict(name=n, msg=f"ERRO transcricao {n[:34]}: {type(e).__name__}")
    etapa("transcrevendo", list(nomes), _t, a.jobs)

    # 3. classificacao
    def _c(n):
        p = f"{W}/cls/{n}.json"
        if os.path.exists(p):
            return dict(name=n, msg=None)
        try:
            j = classify(f"{W}/tx/{n}.json", n, pasta_entrada=ent, regras_extra=a.regras)
            json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return dict(name=n, msg=f"{j['categoria']:12} {n[:38]}")
        except Exception as e:
            return dict(name=n, msg=f"ERRO classificacao {n[:32]}: {type(e).__name__}")
    etapa("classificando", [n for n in nomes if os.path.exists(f"{W}/tx/{n}.json")], _c, a.jobs)

    # 4. corte / copia / descarte
    print(f"\n>> cortando", flush=True)
    rel = []
    for n, src in sorted(nomes.items()):
        cp = f"{W}/cls/{n}.json"
        if not os.path.exists(cp):
            rel.append(dict(name=n, categoria="ERRO", status="SEM_CLASSIFICACAO")); continue
        t = json.load(open(cp, encoding="utf-8"))
        cat = t["categoria"]
        dst = os.path.join(out, n + ".mp4")

        if cat in DESCARTA:
            rel.append(dict(name=n, categoria=cat, status="DESCARTADO", dur=t["dur"],
                            motivo=t.get("justificativa", ""), **_proc(t))); continue
        if cat in PASSA:
            if t["dur"] < MIN_OUT:
                rel.append(dict(name=n, categoria=cat, status="CURTO_DEMAIS", dur=t["dur"],
                                saida=t["dur"], motivo=f"limpo mas so {t['dur']}s",
                                **_proc(t))); continue
            shutil.copy2(src, dst)
            rel.append(dict(name=n, categoria=cat, status="COPIADO", dur=t["dur"],
                            saida=t["dur"], n_segs=1, cortes=[], **_proc(t))); continue

        keep, rem = cutmod.plan(f"{W}/tx/{n}.json", t.get("remover"), t["dur"])
        tot = sum(e - s for s, e in keep)
        if not keep or tot < MIN_OUT:
            rel.append(dict(name=n, categoria=cat, status="CURTO_DEMAIS", dur=t["dur"],
                            saida=round(tot, 1),
                            motivo=f"sobraria so {tot:.1f}s, minimo {MIN_OUT:.0f}s",
                            **_proc(t))); continue
        rc, err = cutmod.render(src, keep, dst)
        if rc != 0:
            rel.append(dict(name=n, categoria=cat, status="ERRO_FFMPEG", dur=t["dur"],
                            motivo=err[-160:], **_proc(t))); continue
        real = cutmod.duration(dst)
        rel.append(dict(name=n, categoria=cat, status="CORTADO", dur=t["dur"],
                        saida=round(real, 1), n_segs=len(keep),
                        cortes=[[round(s, 2), round(e, 2)] for s, e in rem],
                        divergencia=round(real - tot, 2), **_proc(t)))
        print(f"   CORTADO   {t['dur']:5.1f}s -> {real:5.1f}s ({len(keep)} seg) {n[:38]}", flush=True)

    json.dump(rel, open(os.path.join(out, "_relatorio.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    escreve_relatorio(rel, out, camadas)
    resumo(rel, out)

def escreve_relatorio(rel, out, camadas=None):
    prontos = [r for r in rel if r["status"] in ("CORTADO", "COPIADO")]
    fora    = [r for r in rel if r["status"] not in ("CORTADO", "COPIADO")]
    L = ["# Relatorio de cortes", ""]
    L.append(f"Prontos para subir: **{len(prontos)}**  |  Fora: **{len(fora)}**")
    L += ["", "## Prontos", "", "| video | original | editado | cortes |", "|---|---|---|---|"]
    for r in sorted(prontos, key=lambda x: -x.get("dur", 0)):
        c = "copiado inteiro" if r["status"] == "COPIADO" else \
            "; ".join(f"{s}-{e}s" for s, e in r.get("cortes", [])) or "-"
        L.append(f"| {r['name']} | {r.get('dur')}s | {r.get('saida')}s | {c} |")
    if fora:
        L += ["", "## Fora (nao entregues)", "", "| video | motivo |", "|---|---|"]
        for r in fora:
            L.append(f"| {r['name']} | {r['status']}: {r.get('motivo','')[:120]} |")
    avisos = [(r["name"], x) for r in rel for x in (r.get("avisos") or [])]
    if avisos:
        L += ["", "## Avisos", "",
              "Pedidos de regra local que foram ignorados porque tentavam liberar preco ou",
              "mencao ao TikTok. Essa parte e' travada e so muda no repo, com revisao.", ""]
        for n, x in avisos:
            L.append(f"- **{n}**: {x}")
    if camadas:
        L += ["", "## Regras locais aplicadas", ""]
        for rotulo, caminho, _ in camadas:
            L.append(f"- {rotulo}: `{caminho}`")
    L += ["", "---", "",
          "Removido: fala de preco/desconto/promocao e mencao ao TikTok "
          "(TikTok Shop, carrinho laranja, link em cima do nome).",
          "", "Categorias: TRIM = sujeira nas pontas | CORTE_MIOLO = trecho no meio | "
          "LIMPO = nada a cortar | RENARRAR = corte nao resolve (descartado) | "
          "SEM_FALA = sem narracao (descartado)."]
    open(os.path.join(out, "RELATORIO.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

def resumo(rel, out):
    from collections import Counter
    c = Counter(r["status"] for r in rel)
    prontos = [r for r in rel if r["status"] in ("CORTADO", "COPIADO")]
    print("\n" + "=" * 58)
    for k, v in c.most_common():
        print(f"  {k:18} {v}")
    if prontos:
        ent = sum(r.get("dur", 0) for r in prontos)
        sai = sum(r.get("saida", 0) for r in prontos)
        print(f"\n  {len(prontos)} prontos | {ent/60:.1f}min -> {sai/60:.1f}min "
              f"(retencao {100*sai/ent:.0f}%)")
    div = [r for r in rel if abs(r.get("divergencia", 0)) > 0.35]
    if div:
        print(f"  ATENCAO: {len(div)} com duracao divergente do plano")
    print(f"\n  videos: {out}\n  relatorio: {os.path.join(out,'RELATORIO.md')}")
    print("=" * 58)

if __name__ == "__main__":
    main()
