# edits-tts — corte de vídeos de creator para o Meta Ads

Ferramenta da Gocase que pega vídeos de creators do TikTok Shop e corta as partes que não
podem rodar no Meta Ads — menção a preço, desconto, promoção, "carrinho laranja", "link em
cima do meu nome" — deixando o vídeo assistível.

**Você não precisa saber programar pra usar.** Cole o link deste repositório no Claude Code
e peça o setup:

```
aqui está o link do repo: github.com/joaovitormesquita-goca/edits-tts
quero fazer o setup e passar a usar isso no meu Claude Code
```

Depois de instalado, o uso é conversa normal:

```
corta os vídeos que estão em ~/Downloads/videos-de-hoje
```

Você recebe os vídeos cortados numa pasta nova e um `RELATORIO.md` dizendo o que saiu de cada
um e quais vídeos foram descartados, com o motivo.

---

## O que só você pode fazer (o Claude não faz por você)

**Conseguir a chave da API do Gemini.** É uma credencial sua, então o Claude não pega nem
manuseia. Peça uma `GEMINI_API_KEY` no AI Proxy da Gocase e guarde:

1. Crie o arquivo `~/.claude/.env`
2. Escreva nele uma linha: `GEMINI_API_KEY=<a chave>`
3. Salve e rode no Terminal: `chmod 600 ~/.claude/.env`

Duas coisas importantes, e o motivo de cada uma:

- **Não cole a chave numa conversa de chat.** A conversa fica salva no histórico, e quem tiver
  acesso a ela passa a ter acesso à chave.
- **Não use `echo` no Terminal pra escrever a chave.** O Terminal guarda tudo que você digita
  num arquivo de histórico. Use um editor de texto.

Se algo der errado, o Claude tem um comando de diagnóstico que diz exatamente o que falta —
ele nunca mostra a chave, só confirma se ela funciona.

---

## Instruções para o Claude Code

> Esta seção é para o agente. Se você é uma pessoa lendo, pode pular — o Claude segue estes
> passos por você.

São três passos e caminhos fixos. Explique cada um em linguagem simples antes de rodar: a
pessoa provavelmente não é técnica e vai se assustar com saída de terminal sem contexto.

### 1. Instale a ferramenta

Ela vive em `~/.claude/skills/cortar-tiktok/`, que o Claude Code lê sozinho ao iniciar. Não
há plugin pra registrar, nem marketplace, nem cache, nem versão no caminho.

```bash
mkdir -p ~/.claude/skills
curl -sL https://github.com/joaovitormesquita-goca/edits-tts/archive/refs/heads/main.tar.gz \
  | tar xz -C ~/.claude/skills
rm -rf ~/.claude/skills/cortar-tiktok
mv ~/.claude/skills/edits-tts-main ~/.claude/skills/cortar-tiktok
```

`curl` e `tar` já vêm no macOS — não precisa de git nem das ferramentas de linha de comando
do Xcode. Se a pessoa já tiver git, `git clone <repo> ~/.claude/skills/cortar-tiktok` também
serve e deixa a atualização em um `git pull`.

**Avise que ela precisa fechar e abrir o Claude Code**: a skill só entra em contexto quando
ele inicia. O resto do setup funciona antes disso, porque você chama os scripts direto.

### 2. Verifique o ffmpeg e rode o diagnóstico

```bash
python3 ~/.claude/skills/cortar-tiktok/scripts/checar.py
```

Ele confere ffmpeg, Python, a chave e a instalação, e imprime o que falta com o passo a passo
de cada pendência. Sai com código 0 quando está tudo pronto.

Se faltar o ffmpeg — é o programa que corta o vídeo, sem ele nada funciona — instale com
`brew install ffmpeg`, avisando antes que vai instalar um programa e que leva alguns minutos.
Se o `brew` também não existir, **não instale o Homebrew por conta própria**: mande a pessoa
em https://brew.sh e espere, porque essa instalação pede a senha do usuário e é ela que
precisa digitar.

### 3. Conduza a pessoa na chave da API

Se o diagnóstico disser que falta a chave, **não tente resolver sozinho e não peça a chave no
chat.** Manuseio de credencial é da pessoa. Faça assim:

1. Diga que falta a chave, que ela vem do AI Proxy da Gocase, e o porquê de você não poder
   fazer essa parte (é uma credencial dela, e colar no chat deixaria a chave gravada no
   histórico da conversa)
2. Crie o arquivo com a linha pronta pra ela completar, e restrinja a leitura:
   ```bash
   mkdir -p ~/.claude
   [ -f ~/.claude/.env ] || printf 'GEMINI_API_KEY=\n' > ~/.claude/.env
   chmod 600 ~/.claude/.env
   ```
3. Abra o arquivo pra ela colar: `open -e ~/.claude/.env`
4. Explique: colar depois do `=`, sem espaço e sem aspas, e salvar
5. Quando ela disser que colou, rode o diagnóstico de novo. Ele valida a chave contra a API
   sem nunca imprimir o valor.

Com o diagnóstico limpo, diga que está pronto e dê um exemplo de uso com uma pasta que a
pessoa realmente tenha. Se ela tiver vídeos à mão, ofereça rodar num vídeo só primeiro, pra
ela ver o resultado antes de confiar num lote inteiro.

### Os três comandos, para referência

Caminhos fixos — não precisa procurar nada:

```bash
python3 ~/.claude/skills/cortar-tiktok/scripts/checar.py                    # diagnóstico
python3 ~/.claude/skills/cortar-tiktok/scripts/pipeline.py <pasta>          # cortar
python3 ~/.claude/skills/cortar-tiktok/scripts/verificar.py <pasta_saida>   # conferir
```

### Atualizar depois

Mesma instalação de novo (o `rm -rf` no meio troca a versão antiga), ou `git pull` dentro de
`~/.claude/skills/cortar-tiktok` se a instalação foi por git. As regras que a pessoa escreveu
não são afetadas: moram em `~/.claude/cortar-tiktok/regras.md` e nas pastas de lote, fora da
pasta da skill.

---

## Para quem mantém o repo

A raiz do repositório **é** a pasta da skill: `SKILL.md`, `references/` e `scripts/` ficam no
topo, porque a instalação é um `tar xz` direto em `~/.claude/skills/cortar-tiktok/`.

```
SKILL.md                             quando aciona e como rodar
references/regras-gocase.md          o que sai, o que fica, armadilhas
references/regras-locais-exemplo.md  modelo pro time escrever as regras dele
scripts/                             pipeline, verificador, diagnóstico
docs/levantamento-2026-09-10.json    triagem dos 59 vídeos do acervo inicial
```

Mudança publicada aqui chega em quem reinstalar ou der `git pull`. Não existe cache
intermediário, então não há versão pra bumpar — que era a principal fonte de "publiquei a
correção e não chegou em ninguém" no desenho anterior, por plugin.
