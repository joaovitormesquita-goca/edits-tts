# edits-tts — corte de vídeos de creator para o Meta Ads

Ferramenta da Gocase que pega vídeos de creators do TikTok Shop e corta as partes que não
podem rodar no Meta Ads — menção a preço, desconto, promoção, "carrinho laranja", "link em
cima do meu nome" — deixando o vídeo assistível.

**Você não precisa saber programar pra usar.** Cole o link deste repositório no Claude Code
e peça o setup; ele instala o que dá pra instalar e te guia no resto.

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

Quando alguém te apontar este repositório pedindo setup, execute nesta ordem. Explique cada
passo em linguagem simples antes de rodar: a pessoa provavelmente não é técnica e vai se
assustar com saída de terminal sem contexto.

### 1. Verifique o ffmpeg

```bash
ffmpeg -version
```

Se não existir, o ffmpeg é o programa que corta o vídeo — sem ele nada funciona. Instale com
`brew install ffmpeg`, avisando antes que vai instalar um programa e que leva alguns minutos.
Se o `brew` também não existir, **não instale o Homebrew por conta própria**: mande a pessoa
em https://brew.sh e espere, porque essa instalação pede a senha do usuário e é ela que
precisa digitar.

### 2. Instale o plugin

```bash
claude plugin marketplace add joaovitormesquita-goca/edits-tts
claude plugin install cortar-tiktok@edits-tts
```

Isso baixa a skill pro cache local. Nenhuma dependência de Python é necessária — os scripts
usam só biblioteca padrão.

### 3. Rode o diagnóstico

Localize o script. O caminho tem a **versão** no meio, e versões antigas ficam no cache
depois de uma atualização — então não presuma caminho fixo e não pegue o primeiro que
aparecer: ordene por data e use o mais recente.

```bash
find ~/.claude/plugins/cache -path "*cortar-tiktok*" -name checar.py -print0 \
  | xargs -0 ls -t | head -1
```

Rode o caminho que sair daí com `python3`. Vale o mesmo pro `pipeline.py` e o
`verificar.py` — sempre o mais recente, senão você roda uma versão velha da ferramenta
sem perceber (acontece: dá erro nenhum, só se comporta como a versão antiga).

Ele confere ffmpeg, Python, a chave e o plugin, e imprime o que falta com o passo a passo de
cada pendência. Sai com código 0 quando está tudo pronto.

### 4. Conduza a pessoa na chave da API

Se o diagnóstico disser que falta a chave, **não tente resolver sozinho e não peça a chave no
chat.** Manuseio de credencial é da pessoa. Faça assim:

1. Diga que falta a chave, que ela vem do AI Proxy da Gocase, e o porquê de você não poder
   fazer essa parte (é uma credencial dela, e colar no chat deixaria a chave gravada no
   histórico da conversa)
2. Crie o arquivo vazio com a linha pronta pra ela completar, e restrinja a leitura:
   ```bash
   mkdir -p ~/.claude
   [ -f ~/.claude/.env ] || printf 'GEMINI_API_KEY=\n' > ~/.claude/.env
   chmod 600 ~/.claude/.env
   ```
3. Abra o arquivo pra ela colar: `open -e ~/.claude/.env`
4. Explique: colar depois do `=`, sem espaço e sem aspas, e salvar
5. Quando ela disser que colou, rode o diagnóstico de novo. Ele valida a chave contra a API
   sem nunca imprimir o valor.

### 5. Confirme e mostre como usar

Com o diagnóstico limpo, diga que está pronto e dê um exemplo concreto de uso — de
preferência com uma pasta que a pessoa realmente tenha. Se ela tiver vídeos à mão, ofereça
rodar num vídeo só primeiro, pra ela ver o resultado antes de confiar num lote inteiro.

### Atualizar depois

Não existe `claude plugin update`. Como o cache só é refeito quando a `version` do
`plugin.json` muda, a sequência é:

```bash
claude plugin marketplace update edits-tts
claude plugin uninstall cortar-tiktok@edits-tts
claude plugin install cortar-tiktok@edits-tts
```

---

## Para quem mantém o repo

Ao publicar mudança na skill, **bumpe `version` em
`plugins/cortar-tiktok/.claude-plugin/plugin.json`**. Sem isso o cache de quem já instalou não
é refeito e a correção não chega em ninguém — testado, é assim que se comporta.

Valide o manifesto antes de publicar:

```bash
claude plugin validate .
```

Estrutura:

```
.claude-plugin/marketplace.json          catálogo do marketplace
plugins/cortar-tiktok/
├── .claude-plugin/plugin.json           manifesto e VERSÃO
└── skills/cortar-tiktok/
    ├── SKILL.md                         quando aciona e como rodar
    ├── references/regras-gocase.md      o que sai, o que fica, armadilhas
    └── scripts/                         pipeline, verificador, diagnóstico
docs/levantamento-2026-09-10.json        triagem dos 59 vídeos do acervo inicial
```

Para registrar o marketplace automaticamente em quem já usa um repo do time, adicione ao
`.claude/settings.json` do projeto:

```json
{
  "extraKnownMarketplaces": {
    "edits-tts": {
      "source": { "source": "github", "repo": "joaovitormesquita-goca/edits-tts" }
    }
  }
}
```

O repo deve ser **privado**: contém regra de negócio e a lista de termos de preço da operação.
