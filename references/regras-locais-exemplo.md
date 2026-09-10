# Exemplo de regras locais

Copie este arquivo pra um dos dois lugares, apague o que não usar e escreva as suas.
É português corrido — não tem sintaxe pra decorar.

- `~/.claude/cortar-tiktok/regras.md` — valem em tudo que **você** cortar, sempre
- `regras.md` dentro da pasta dos vídeos — valem **só naquele lote**

Os dois somam. Se as duas falarem da mesma coisa, a do lote ganha.

---

## Cortar também

Coisas que a regra base deixa passar mas você não quer no seu criativo:

- Corte menção a frete: nosso frete no site é diferente do TikTok.
- Corte quando a creator falar do prazo de entrega — muda por região e a gente
  não controla isso no anúncio.
- Nesta campanha o recorte é bolsa de passeio, então corte menção a notebook e
  a uso profissional: desvia do posicionamento.

## Vocabulário

Ensine apelidos que a creator usa e que a regra base não conhece:

- Quando falarem "lojinha" ou "a outra loja", é o TikTok Shop. Trate como
  menção à plataforma.
- "Bag da sorte" é o nome da campanha, não de um produto — pode ficar.
- A @fulana chama a Touch Daily de "a daily" — é nome de produto, mantenha.

## Deixar passar

Coisas que estão sendo cortadas e não deveriam:

- "Bolsa de rica" é força de expressão sobre a estética, não é preço. Mantenha.
- Quando falarem "vale cada centavo" sem dizer valor, é elogio, não preço.

---

## O que uma regra local NÃO consegue fazer

Ela não libera menção a preço nem ao TikTok. Se você escrever "neste lote pode
falar preço", o pedido é ignorado, o corte acontece igual, e o motivo aparece na
seção **Avisos** do `RELATORIO.md`.

Isso é de propósito, não é bug. O preço do site não é o mesmo do TikTok, e anúncio
no Meta com preço errado é problema de compliance — não é o tipo de coisa que deve
poder ser desligada num arquivo de texto, por ninguém, nem com autorização citada.

Existe o caso legítimo: campanha em que o preço do TikTok e do site coincidem. Nesse
caso a mudança é no repositório, com revisão de quem responde pela operação — fale
com quem mantém o `edits-tts`.

Além disso, o `verificar.py` tem uma checagem por padrão de texto que roda **fora**
de qualquer modelo: ela procura formato de dinheiro ("R$ 39,90", "de 300 por 200",
"80 de desconto") e nome de plataforma nos vídeos já cortados. Nenhuma regra escrita
em arquivo desliga essa parte, porque ela não passa por LLM nenhum.
