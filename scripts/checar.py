#!/usr/bin/env python3
"""Diz o que ja esta pronto e o que falta pra usar o cortar-tiktok.

Nao instala nada e nao imprime a chave -- so confere e explica em portugues claro.
Sai com codigo 0 se estiver tudo pronto, 1 se faltar algo.

  python3 scripts/checar.py
"""
import os, sys, json, shutil, subprocess, urllib.request

WIN = sys.platform.startswith("win")
MAC = sys.platform == "darwin"

def _instala_ffmpeg():
    if WIN:
        return ("Instalar o ffmpeg. No PowerShell:  winget install Gyan.FFmpeg\n"
                "     Depois FECHE E ABRA o PowerShell (e o app do Claude), senao ele nao\n"
                "     acha o programa novo. Se 'winget' nao existir, baixe em ffmpeg.org.")
    if MAC:
        return ("Instalar o ffmpeg. No Terminal:  brew install ffmpeg\n"
                "     (se disser que 'brew' nao existe, instale o Homebrew primeiro em brew.sh)")
    return ("Instalar o ffmpeg pelo gerenciador da sua distro, por exemplo:\n"
            "       sudo apt install ffmpeg      (Debian/Ubuntu)\n"
            "       sudo dnf install ffmpeg      (Fedora)")

def _protege(caminho):
    """Como restringir a leitura do arquivo da chave, no sistema de cada um."""
    if WIN:
        return (f'icacls "{caminho}" /inheritance:r /grant:r "%USERNAME%:R"')
    return f"chmod 600 {caminho}"

def _editor(caminho):
    return f'notepad "{caminho}"' if WIN else f"open -e {caminho}"

def _instala_skill():
    destino = os.path.expanduser("~/.claude/skills")
    if WIN:
        return ("Instalar a ferramenta. No PowerShell, uma linha:\n"
                "       mkdir -Force ~\\.claude\\skills; "
                "curl.exe -sL https://github.com/joaovitormesquita-goca/edits-tts/archive/refs/heads/main.tar.gz "
                "-o $env:TEMP\\e.tgz; tar.exe xzf $env:TEMP\\e.tgz -C ~\\.claude\\skills; "
                "Remove-Item -Recurse -Force ~\\.claude\\skills\\cortar-tiktok -EA 0; "
                "Move-Item ~\\.claude\\skills\\edits-tts-main ~\\.claude\\skills\\cortar-tiktok")
    return ("Instalar a ferramenta. No Terminal, uma linha:\n"
            "       mkdir -p ~/.claude/skills && curl -sL "
            "https://github.com/joaovitormesquita-goca/edits-tts/archive/refs/heads/main.tar.gz "
            "| tar xz -C ~/.claude/skills && rm -rf ~/.claude/skills/cortar-tiktok && "
            "mv ~/.claude/skills/edits-tts-main ~/.claude/skills/cortar-tiktok")

OK, FALTA, AVISO = "  [ok]   ", "  [falta]", "  [aviso]"
problemas = []

def diz(marca, texto):
    print(f"{marca} {texto}")

SISTEMA = "Windows" if WIN else ("macOS" if MAC else "Linux")
print(f"\nConferindo o que falta pro cortar-tiktok funcionar ({SISTEMA})...\n")

# 1. ffmpeg -- o programa que corta o video
if shutil.which("ffmpeg") and shutil.which("ffprobe"):
    v = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    diz(OK, f"ffmpeg instalado ({v.split()[2] if len(v.split()) > 2 else 'ok'})")
else:
    diz(FALTA, "ffmpeg — e o programa que corta o video")
    problemas.append(_instala_ffmpeg())

# 2. python
if sys.version_info >= (3, 9):
    diz(OK, f"Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    diz(FALTA, f"Python 3.9 ou mais novo (voce tem {sys.version.split()[0]})")
    problemas.append("Atualizar o Python: baixe em python.org/downloads"
                     + (" e marque 'Add python.exe to PATH' no instalador." if WIN else "."))

# 3. a chave da API
def acha_chave():
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return "variavel de ambiente", os.environ["GEMINI_API_KEY"].strip()
    locais = [os.path.join(os.getcwd(), ".env"), os.path.expanduser("~/.claude/.env")]
    for p in locais:
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return p, v
    return None, None

onde, chave = acha_chave()
if not chave:
    diz(FALTA, "chave da API do Gemini — e o que le o audio dos videos")
    problemas.append(
        "Colocar a chave da API. Isso e a unica coisa que o Claude nao pode fazer por voce,\n"
        "     porque envolve uma credencial sua. Passo a passo:\n"
        "       1. peca uma GEMINI_API_KEY no AI Proxy da Gocase\n"
        f"       2. crie o arquivo {os.path.expanduser('~/.claude/.env')}\n"
        "       3. escreva nele uma linha:  GEMINI_API_KEY=<a chave>\n"
        f"       4. salve e restrinja a leitura:  {_protege(os.path.expanduser('~/.claude/.env'))}\n"
        "     Nao cole a chave no chat e nao escreva ela por linha de comando: nos dois\n"
        "     fica guardada em lugar que outras pessoas ou programas podem ler.")
else:
    diz(OK, f"chave da API encontrada em {onde}")
    # confere se autentica, sem nunca imprimir o valor
    try:
        r = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models",
                                   headers={"x-goog-api-key": chave})
        d = json.load(urllib.request.urlopen(r, timeout=30))
        nomes = [m["name"].split("/")[-1] for m in d.get("models", [])]
        if any("transcribe" in n for n in nomes):
            diz(OK, "chave funciona e tem acesso ao modelo de transcricao")
        else:
            diz(AVISO, "chave funciona, mas nao vi o modelo de transcricao na conta")
            problemas.append(
                "A chave autentica, mas o modelo 'gemini-3.5-transcribe' nao aparece nela.\n"
                "     Confirme com quem cuida do AI Proxy se a chave tem acesso a esse modelo.")
    except Exception as e:
        diz(FALTA, "a chave nao foi aceita pela API")
        problemas.append(
            f"A chave existe mas foi recusada ({type(e).__name__}). Provavelmente foi copiada\n"
            "     incompleta, esta com espaco sobrando, ou foi revogada. Peca uma nova.")

# 4. a skill instalada no lugar certo
SKILL_DIR = os.path.expanduser("~/.claude/skills/cortar-tiktok")
if os.path.exists(os.path.join(SKILL_DIR, "SKILL.md")):
    diz(OK, f"skill instalada em ~/.claude/skills/cortar-tiktok")
else:
    diz(FALTA, "a ferramenta ainda nao esta instalada")
    problemas.append(_instala_skill())

print()
if problemas:
    print("=" * 66)
    print(f"  Falta {len(problemas)} coisa(s). O que fazer:\n")
    for i, p in enumerate(problemas, 1):
        print(f"  {i}. {p}\n")
    print("  Depois de resolver, rode este comando de novo pra confirmar.")
    print("=" * 66)
    sys.exit(1)
print("=" * 66)
print("  Tudo pronto. Pra usar, diga ao Claude algo como:")
print('    "corta os videos que estao na pasta ~/Downloads/videos-de-hoje"')
print("=" * 66)
