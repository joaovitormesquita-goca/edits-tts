"""Parametros e credencial. Ajuste aqui, nao no meio dos scripts."""
import os

# --- corte ---
MIN_SEG  = 0.60   # sobra menor que isso e' fragmento, descarta
MIN_OUT  = 8.0    # saida menor que isso nao serve como anuncio
SNAP_TOL = 0.40   # distancia maxima pra puxar o corte pra dentro de uma pausa
FADE     = 0.02   # 20ms de fade nas emendas; sem isso a emenda estala
PAD      = 0.03   # respiro em volta da fala preservada
PAUSA_MIN = 0.10  # gap de audio que conta como pausa

# --- modelos ---
MODEL_ASR = "gemini-3.5-transcribe"
MODEL_CLS = "gemini-flash-latest"
BASE = "https://generativelanguage.googleapis.com"

def _busca_env(d):
    """Sobe a arvore de pastas a partir de d procurando GEMINI_API_KEY num .env"""
    for _ in range(8):
        p = os.path.join(d, ".env")
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd
    return None

def load_key():
    """Procura a chave no ambiente, depois num .env subindo a arvore -- primeiro a
    partir da pasta onde o comando foi rodado, depois a partir da propria skill,
    pra funcionar mesmo se o time rodar de outro diretorio.
    Nunca imprime o valor: se faltar, diz onde colocar."""
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    candidatos = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for origem in candidatos:
        v = _busca_env(origem)
        if v:
            return v
    # a skill vive em ~/.claude/skills, fora do projeto: aceita chave no home
    for p in (os.path.expanduser("~/.claude/.env"), os.path.expanduser("~/.gocase.env")):
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
    raise SystemExit(
        "GEMINI_API_KEY nao encontrada.\n"
        "Coloque a chave em UM destes lugares:\n"
        "  1. .env na pasta do projeto      (uso no projeto)\n"
        "  2. ~/.claude/.env                (uso em qualquer pasta)\n"
        "Formato da linha:  GEMINI_API_KEY=<sua chave>\n"
        "Depois restrinja a leitura:  chmod 600 <arquivo>"
    )


# --- regras em camadas ---------------------------------------------------
# A regra base vive no prompt do classify.py (versionada, chega por atualizacao
# versionado no repo). Em cima dela, cada pessoa pode escrever a sua. Esses arquivos
# ficam FORA da pasta da skill de proposito: atualizar a ferramenta substitui essa
# pasta, e regra escrita lá dentro seria perdida.
REGRAS_PESSOA = os.path.expanduser("~/.claude/cortar-tiktok/regras.md")
REGRAS_LOTE   = "regras.md"   # dentro da pasta de entrada, vale so pra aquele lote

def carrega_regras(pasta_entrada=None, extra=None):
    """Junta as regras locais, da mais geral pra mais especifica.
    Precedencia entre as camadas locais: pessoa < lote < --regras.

    Nenhuma delas afrouxa o nucleo (preco e plataforma): o nucleo e' travado, e
    regra local so pode APERTAR (somar coisa a cortar) ou corrigir vocabulario
    ("lojinha" = TikTok Shop). Isso e' escolha de operacao: subir anuncio com
    preco errado custa mais do que pedir um PR nas raras campanhas de preco
    equalizado. Quem precisa afrouxar mexe no repo, com revisao."""
    camadas = []
    cands = [("suas regras", REGRAS_PESSOA)]
    if pasta_entrada:
        cands.append(("regras deste lote", os.path.join(pasta_entrada, REGRAS_LOTE)))
    if extra:
        cands.append(("regras passadas no comando", extra))
    for rotulo, caminho in cands:
        if caminho and os.path.exists(caminho):
            txt = open(caminho).read().strip()
            if txt:
                camadas.append((rotulo, caminho, txt))
    return camadas
