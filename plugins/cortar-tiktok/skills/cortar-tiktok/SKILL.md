---
name: cortar-tiktok
description: Corta vídeos de creators do TikTok Shop da Gocase para reaproveitar como criativo no Meta Ads, removendo toda menção a preço, desconto, promoção e à plataforma TikTok (TikTok Shop, carrinho laranja, "link em cima do meu nome"). Use sempre que alguém pedir para preparar, adaptar, limpar, cortar ou aproveitar vídeo de creator/UGC/TikTok Shop para o Meta, Instagram ou Facebook — inclusive quando disserem apenas "tira o preço desses vídeos", "adapta esses vídeos pro Meta", "esses vídeos falam de TikTok, arruma", "prepara o lote de hoje dos creators" ou apontarem uma pasta de vídeos baixados do TikTok. Use também quando pedirem para conferir se um vídeo já cortado ainda tem menção a preço ou TikTok.
---

# Cortar vídeos do TikTok Shop para Meta Ads

## O problema que isso resolve

A Gocase vende no TikTok Shop e no site próprio, **com preços diferentes**. Os creators do
TikTok gravam falando do preço de lá, do "carrinho laranja" e do "link em cima do meu nome".
Esse material é bom — é UGC real, com produto na mão — mas do jeito que está não pode rodar
no Meta Ads: o preço não confere com o site e a menção à plataforma concorrente não faz sentido
num anúncio que leva pro site.

O trabalho é remover essas falas mantendo o vídeo assistível. Feito à mão no CapCut, é lento
e não escala com o volume diário. Esta skill automatiza o corte.

## Escopo: só corte

Esta skill **corta e nada mais**. Não gera narração nova, não escreve hook, não põe legenda,
não faz upscale. Vídeo que só se salvaria com narração nova é descartado e reportado — é
decisão consciente de manter o básico bem feito antes de complicar.

## Antes de rodar

Duas coisas precisam existir:

1. **ffmpeg** instalado (`ffmpeg -version`). Se faltar: `brew install ffmpeg`.
2. **`GEMINI_API_KEY`**, em `.env` na raiz do projeto **ou** em `~/.claude/.env` (este
   segundo funciona de qualquer pasta, útil quando a skill vem instalada como plugin):
   ```
   GEMINI_API_KEY=<a chave>
   ```
   Nunca peça a chave por chat nem escreva ela via `echo`/`export` no terminal — vai parar no
   histórico do shell. O arquivo deve estar no `.gitignore` e com permissão `600`.

Python: só biblioteca padrão. Não precisa instalar dependência nenhuma.

## Como rodar

Os scripts ficam na pasta `scripts/` ao lado deste `SKILL.md`. Use o caminho da própria skill
— ele muda conforme a instalação (dentro do projeto em `.claude/skills/cortar-tiktok/`, ou no
cache de plugins quando distribuída via marketplace), então não presuma um caminho fixo:
resolva a partir de onde este arquivo está.

Um comando, apontando pra pasta com os vídeos crus (procura `.mp4` recursivamente, então
pasta com subpastas por data funciona):

```bash
python <pasta_da_skill>/scripts/pipeline.py <pasta_de_entrada>
```

Saída padrão: `<pasta_de_entrada>/../cortados`. Para escolher outra, use `--out <pasta>`.
Para mais paralelismo nas chamadas de API, `--jobs 6`.

O processamento é em quatro etapas: extrai áudio → transcreve com timestamp por palavra →
classifica o que remover → corta. Tudo fica em cache em `<saida>/_trabalho`, então rodar de
novo na mesma pasta só processa vídeo novo. Isso importa: transcrever de novo custa dinheiro
e tempo à toa.

## Depois de rodar, verifique

`ffmpeg` sair com código 0 prova que o arquivo foi escrito, não que o corte ficou limpo.
A checagem que vale é re-transcrever a saída e reler:

```bash
python <pasta_da_skill>/scripts/verificar.py <pasta_de_saida>
```

Por padrão confere uma amostra, priorizando os vídeos com mais emendas (onde o risco é maior).
`--todos` roda no lote inteiro. Ele avisa em qual vídeo sobrou violação e onde.

Rode isso sempre antes de entregar o lote, e relate o resultado. Se sobrou violação em algum,
diga qual e o que sobrou — não entregue um lote dizendo que está limpo sem ter verificado.

## Como ler o resultado

`RELATORIO.md` na pasta de saída lista os prontos (com o que foi cortado de cada um) e os que
ficaram fora, com motivo. Os baldes:

| Categoria | O que é | Destino |
|---|---|---|
| `TRIM` | Violação só nas pontas (hook de preço no início, CTA no fim) | Corta as pontas |
| `CORTE_MIOLO` | Violação isolada no meio | Corta o trecho |
| `LIMPO` | Nada a cortar | Copiado inteiro |
| `RENARRAR` | Violação entranhada no roteiro todo | **Descartado** |
| `SEM_FALA` | Sem narração (só música) | **Descartado** |
| `CURTO_DEMAIS` | Sobraria menos que o mínimo de anúncio | **Descartado** |

`TRIM` é o caso dominante, porque o formato típico do creator é
`hook de preço → review do produto → CTA do TikTok`: a sujeira mora nas pontas e o miolo é
review limpo.

Vídeo em `RENARRAR` concentrado num mesmo creator é sinal de formato, não de azar — vale
pedir pra essa pessoa gravar um trecho de fala genérica sem preço, e o material dela volta
a ser aproveitável.

## Ajustar as regras

A regra base está em `references/regras-gocase.md`, junto com as armadilhas já descobertas
(nomes que a transcrição erra, e o "carrinho" que é de bebê e não do TikTok). Leia esse
arquivo antes de mexer nas regras ou quando o resultado parecer errado — quase todo falso
positivo/negativo já está catalogado lá.

**Cada pessoa pode escrever as suas em cima da base**, em português corrido, sem tocar em
código. O pipeline lê dois arquivos, se existirem, e os soma à regra base:

| Arquivo | Alcance |
|---|---|
| `~/.claude/cortar-tiktok/regras.md` | tudo que essa pessoa cortar, sempre |
| `regras.md` na pasta de entrada | só aquele lote |

Também dá pra passar um avulso com `--regras <arquivo>`. Se houver conflito, o mais
específico ganha: pessoa < lote < `--regras`.

Esses arquivos moram **fora** do plugin de propósito. O cache do plugin é recriado a cada
versão nova, então regra escrita lá dentro seria apagada na primeira atualização.

Quando alguém pedir ajuda pra criar as regras dela, mostre
`references/regras-locais-exemplo.md` — é um modelo comentado pra copiar. E se o pedido dela
for **capacidade nova** (legenda, upscale, re-narração) e não critério de corte, isso não é
regra: é uma skill nova, e deve entrar como outro plugin no marketplace.

### O núcleo é travado

Regra local pode **apertar** (mandar cortar mais) e **corrigir vocabulário** (ensinar que
"lojinha" é o TikTok Shop). Não pode liberar menção a preço nem à plataforma — nem com
autorização citada. Pedido desse tipo é ignorado, o corte acontece igual, e o motivo entra na
seção **Avisos** do `RELATORIO.md`.

Se alguém questionar, o motivo é: preço do site ≠ preço do TikTok, e anúncio no Meta com
preço errado é compliance, não performance. Afrouxar isso exige mudança no repo, com revisão.
O caso legítimo (campanha de preço equalizado) existe e é atendido por lá.

Os parâmetros de corte ficam no topo de `scripts/config.py`, com o motivo de cada um:
duração mínima de saída, tolerância do snap em pausa, duração do fade nas emendas.

## Por que a decisão é de um modelo e não de uma lista de palavras

Tentador filtrar por palavra-chave, mas erra nas duas direções, e isso já foi medido neste
material:

- a transcrição escreve "Shein Talk Shop" no lugar de "TikTok Shop" — uma busca por `tiktok`
  deixa passar;
- "cabe tudo o que eu **preciso**" casa com uma busca por `prec` e some fala boa;
- "alça pra encaixar **no carrinho**" numa mochila de maternidade é carrinho de **bebê** —
  cortar isso destrói uma fala legítima do produto.

Quem decide é o modelo lendo a frase em contexto. As regras que ele aplica estão no prompt em
`scripts/classify.py`.

## Se der problema

**"GEMINI_API_KEY nao encontrada"** — falta o `.env`, ou você está rodando de uma pasta fora
da árvore do projeto.

**Muita coisa em `RENARRAR`** — pode ser regra apertada demais. Confira alguns casos no
`RELATORIO.md`: se a justificativa não convence, ajuste as regras em
`references/regras-gocase.md` e no prompt do `classify.py`, e rode de novo apagando
`<saida>/_trabalho/cls` (mantendo `tx`, pra não re-transcrever).

**Corte soando picado** — aumente `SNAP_TOL` no `config.py` pra dar mais liberdade de puxar
o corte pra dentro de uma pausa. Se o estalo persistir, aumente `FADE`.

**Saída com duração diferente do plano** — o resumo avisa. Normalmente é vídeo com áudio e
vídeo de durações diferentes na origem; vale checar o arquivo cru.
