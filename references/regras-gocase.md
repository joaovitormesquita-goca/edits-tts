# Regras de corte — Gocase TikTok Shop → Meta Ads

Este arquivo é a fonte de verdade sobre **o que sai e o que fica**. O prompt em
`scripts/classify.py` implementa estas regras; se você mudar uma coisa aqui, mude lá também.

## Por que existe uma regra de preço

Preço do TikTok Shop ≠ preço do site. O anúncio no Meta leva pro site. Qualquer número de
preço dito no vídeo passa a ser informação errada — e propaganda com preço que não confere
é problema de compliance, não só de performance.

Por isso a regra é **qualquer** menção a preço, não só preço divergente: não dá pra confiar
que a pessoa conferiu a tabela, e o preço do site muda.

---

## Sai (violação)

### Preço e oferta
- valor em reais, dito ou implícito: "R$ 39,90", "estava de 300 e agora por 200", "menos R$100"
- desconto, promoção, cupom, "promoção relâmpago", "valor promocional"
- comparação de preço: "mais barato que no site", "sai muito mais caro lá", "metade do preço"
- frete grátis, parcelamento, "à vista"

### Plataforma TikTok e seus mecanismos
- "TikTok", "TikTok Shop", "aqui no TikTok"
- "carrinho laranja", "no carrinho" (quando é o carrinho da loja)
- "link em cima do meu nome", "link aqui embaixo", "linkzinho", "clica no link"
- "loja oficial no TikTok", "na live", "cupom da live"

---

## Fica (não é violação)

Cortar essas coisas desperdiça material bom. Cada item aqui é um erro que já aconteceu:

| Fala | Por que fica |
|---|---|
| "cabe tudo o que eu **preciso**" | verbo *precisar*, não substantivo *preço* |
| "a bolsa que a gente **precisa** ter" | idem |
| "não compro Gocase porque é **caro**" | objeção **sem** dizer preço — costuma ser hook bom |
| "alça pra encaixar **no carrinho**" (mochila/bolsa de maternidade) | carrinho de **bebê**, não o carrinho laranja |
| "**original** da Gocase" | atributo de produto |
| "vai **esgotar** logo", "voltou pro estoque" | escassez sem preço nem plataforma |
| qualidade, tamanho, cores, material, compartimentos, uso | é justamente o conteúdo que a gente quer |

### O caso do "carrinho"

O catálogo tem mochila e bolsa de maternidade. Nesses vídeos, "carrinho" aparece como
carrinho de bebê — *"tem alça pra você encaixar no carrinho, não fica carregando peso"*.
É fala legítima de produto e **deve ser mantida**.

Distinção prática: carrinho do TikTok vem junto de link, compra ou preço ("deixa no carrinho
laranja", "clica no carrinho"). Carrinho de bebê vem junto de alça, encaixe, passeio, bebê.
Se o produto é de maternidade, a presunção é carrinho de bebê.

---

## Erros de transcrição já observados

A transcrição erra nomes de forma previsível. Por isso a decisão não pode ser por
palavra-chave — a palavra literal muitas vezes não está lá.

**Viram TikTok:** "Shein Talk Shop", "Talk Shop", "Tik Tok", "TikTok Shopee"

**Viram Gocase** (e são a MARCA, não violação): "Goldcase", "Gold Case", "Bocase", "Golden",
"Agokase", "GoCase"

**Nomes de produto que costumam sair certos:** Touch Moon, Touch Daily, Touch Mini Clear,
Joy Pro, Tote Mini, Tote Puff, Totetale

> Limitação conhecida da API: vocabulário customizado (que resolveria os nomes de produto)
> **não pode** ser combinado com timestamp por palavra. Como o timestamp é o que permite
> cortar, ele ganha. Se a precisão dos nomes virar problema, a saída é dois passes — um com
> vocabulário pro texto, outro com timestamp pro tempo — e casar os dois.

---

## Como cortar bem

**Corte a frase inteira, não a palavra.** Meia frase soa picado e o espectador percebe. Se
a violação está no meio de uma frase, a frase toda sai.

**O corte cai numa pausa.** O `cut.py` puxa o ponto de corte pro meio da pausa mais próxima
(até 0,40s de distância). Sem isso, o corte pega o ataque ou a cauda de uma palavra e fica
audível. As pausas neste material têm tipicamente 140–640ms, folga suficiente.

**Fade de 20ms em cada emenda.** Junção de áudio em amplitude diferente estala. O fade
resolve e é curto o bastante pra ninguém notar.

**Vídeo é corte seco.** O material é B-roll de produto sem rosto falando, então jump cut lê
como edição normal. Não vale complicar com transição.

---

## Limites de qualidade

**Mínimo de saída: 8s** (`MIN_OUT` no `config.py`). Abaixo disso não é anúncio, é toco.
Vídeo que sobraria menos que isso vai pro descarte com o motivo no relatório.

**Resolução de origem: 576x1024.** Abaixo do recomendado pelo Meta (1080x1920). Não é coisa
que o corte resolva — vem do scraper pegando um format ruim. O certo é corrigir na origem;
upscale não cria informação que não foi baixada.

**Final pendurado.** Cortar o CTA às vezes deixa o vídeo terminando numa frase solta (ex:
"então vai esgotar"). Não é violação e a skill não trata. Se incomodar, o ajuste é escolher
um ponto de corte final anterior.

---

## Camadas: base, pessoa, lote

Este arquivo é a **base** — versionada no repo, chega no time quando a ferramenta é atualizada.
Em cima dela cada pessoa escreve as suas, em português, sem tocar em código:

1. **base** (aqui, e no prompt do `classify.py`)
2. **`~/.claude/cortar-tiktok/regras.md`** — da pessoa, valem sempre
3. **`regras.md` na pasta de entrada** — do lote, valem só ali

Somam de cima pra baixo; no conflito, o mais específico ganha. Modelo comentado para copiar:
`references/regras-locais-exemplo.md`.

Os arquivos 2 e 3 ficam fora da pasta da skill porque atualizar a ferramenta substitui essa
pasta — regra escrita lá dentro seria perdida.

### Núcleo travado

Camada local pode **apertar** (somar coisa a cortar) e **corrigir vocabulário** (apelidos que
a creator usa). **Não pode liberar** menção a preço ou à plataforma, nem alegando autorização.
Tentativa é ignorada, o corte acontece, e o motivo vai pra seção *Avisos* do `RELATORIO.md`.

Isso é decisão de operação: subir anúncio com preço errado custa mais do que pedir um PR nas
raras campanhas de preço equalizado.

**Honestidade sobre a força da tranca:** o núcleo é uma instrução no prompt. Ela segura o caso
real — alguém escrevendo "neste lote pode falar preço" — e isso foi testado. O que ela não é:
garantia dura contra um texto local escrito de propósito pra driblar a instrução. Por isso o
`verificar.py` tem uma segunda checagem, por padrão de texto, que roda **fora** de qualquer
modelo: procura formato de dinheiro (`R$ 39,90`, `de 300 e agora por 200`, `80 de desconto`,
`por apenas 99`) e nome de plataforma nas saídas já cortadas. Nenhuma regra em arquivo desliga
essa parte. Ela tem falso positivo por construção — é alerta pra revisão humana, não veredito.

Cobertura conferida em 15 casos, incluindo os negativos que importam: `24 L`, `8 kg`,
`3 bolsos`, "cabe tudo o que eu **preciso**" e "encaixar **no carrinho**" (bebê) não disparam.
