#!/usr/bin/env python3
"""Confere se sobrou violacao nos videos JA cortados.

Existe porque ffmpeg sair com codigo 0 nao prova nada sobre o conteudo: prova que
o arquivo foi escrito. A unica checagem que vale e' ouvir de novo -- ou seja,
re-transcrever a saida e reler. Amostra por padrao; --todos para o lote inteiro.

  python scripts/verificar.py <pasta_de_saida> [--n 6] [--todos]
"""
import os, sys, json, glob, argparse, re, subprocess
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import norm
from gem_asr import transcribe
from classify import classify

# Rede deterministica, independente de qualquer regra local e de qualquer modelo.
# Existe porque o nucleo travado e' uma instrucao de prompt: ela segura o caso real
# (alguem escrevendo "pode liberar preco no lote"), mas nao e' garantia dura contra
# um texto local deliberadamente adversarial. Estes padroes nao passam por LLM
# nenhum, entao nao ha o que instruir pra desligar.
DINHEIRO = re.compile(
    r"(r\$ ?\d"                              # R$ 39,90
    r"|\d+ ?(reais|conto|pila)\b"             # 100 reais
    r"|\bde \d+[^.!?]{0,25}?\b(por|pra|para) \d+"   # "de 300 e agora por 200"
    r"|\b(menos|caiu|abaixou|desconto de) (de )?r?\$? ?\d+"  # "menos 200", "desconto de 80"
    r"|\d+ de (desconto|off)"                # "80 de desconto"
    r"|\bpor (apenas|so|s[oó]) ?\d+"          # "por apenas 99"
    r")", re.I)
PLATAFORMA = re.compile(r"(tiktok|tik tok|talk shop|carrinho laranja)", re.I)

def rede(texto):
    """-> lista de achados crus. Falso positivo aqui e' aceitavel: e' um alerta
    pra revisao humana, nao um veredito."""
    achados = []
    for rotulo, rx in (("preco", DINHEIRO), ("plataforma", PLATAFORMA)):
        for m in rx.finditer(texto or ""):
            ini = max(0, m.start() - 45)
            achados.append((rotulo, texto[ini:m.end() + 45].strip()))
    return achados

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("saida")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--todos", action="store_true")
    a = ap.parse_args()
    out = os.path.abspath(a.saida)
    V = os.path.join(out, "_trabalho", "verificacao")
    os.makedirs(V, exist_ok=True)

    mp4 = [f for f in sorted(glob.glob(os.path.join(out, "*.mp4")))]
    if not mp4:
        raise SystemExit(f"nenhum .mp4 em {out}")
    # prioriza os que tiveram corte de verdade (mais risco de emenda ruim)
    rel = {}
    rp = os.path.join(out, "_relatorio.json")
    if os.path.exists(rp):
        rel = {r["name"]: r for r in json.load(open(rp))}
    def risco(p):
        r = rel.get(os.path.splitext(os.path.basename(p))[0], {})
        return (-(r.get("n_segs") or 1), -(r.get("dur", 0) - r.get("saida", 0)))
    alvo = mp4 if a.todos else sorted(mp4, key=risco)[:a.n]
    print(f"verificando {len(alvo)} de {len(mp4)} videos\n")

    def _v(p):
        n = os.path.splitext(os.path.basename(p))[0]
        mp3 = os.path.join(V, n + ".mp3")
        if not os.path.exists(mp3):
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", p, "-vn",
                            "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-q:a", "5", mp3],
                           capture_output=True)
        tx = os.path.join(V, n + ".json")
        if not os.path.exists(tx):
            json.dump(transcribe(mp3), open(tx, "w"), ensure_ascii=False)
        c = classify(tx, n)
        d = norm.load(tx)
        return n, c, d

    ruim, alertas = [], []
    with cf.ThreadPoolExecutor(4) as ex:
        for n, c, d in ex.map(_v, alvo):
            limpo = c["categoria"] in ("LIMPO", "SEM_FALA")
            crus = rede(d["text"])
            marca = "OK " if (limpo and not crus) else "SUJO"
            print(f"{marca}  {c['categoria']:12} {d['dur']:5.1f}s  {n[:42]}")
            if not limpo:
                ruim.append((n, c))
                for r in (c.get("remover") or []):
                    print(f"        sobrou {r.get('start')}-{r.get('end')}s ({r.get('motivo')})")
            for rotulo, trecho in crus:
                alertas.append((n, rotulo, trecho))
                print(f"        REDE [{rotulo}]: ...{trecho}...")
            print(f"        {d['text'][:200]}")
    print("\n" + "=" * 58)
    if alertas:
        print(f"  A rede deterministica achou {len(alertas)} trecho(s) suspeito(s).")
        print("  Ela nao passa por modelo nenhum, entao regra local nao a desliga.")
        print("  Pode ter falso positivo -- confira de ouvido antes de subir:")
        for n, rotulo, trecho in alertas:
            print(f"    [{rotulo}] {n[:34]}: ...{trecho[:70]}...")
        print()
    if ruim:
        print(f"  {len(ruim)}/{len(alvo)} ainda tem violacao -- revise antes de subir:")
        for n, c in ruim:
            print(f"    {n}: {c.get('justificativa','')[:90]}")
    elif not alertas:
        print(f"  {len(alvo)}/{len(alvo)} limpos: nenhuma mencao a preco ou TikTok sobrou.")
    print("=" * 58)

if __name__ == "__main__":
    main()
