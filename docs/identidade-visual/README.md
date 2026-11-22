# Identidade visual da Pauta

A Pauta transforma a gravação de uma aula de inglês em atividades por aluno e em um plano para a próxima aula.
Quem usa é o professor, em casa ou na sala dos professores, e leva o resultado impresso para a sala de aula.
Esta identidade nasce desse objeto: a folha de papel que o professor corrige, entrega e arquiva.

A fonte única dos valores é [`telecom/web/static/styles.css`](../../telecom/web/static/styles.css). Este documento explica
as escolhas e as regras de uso. Se os dois divergirem, o CSS vale e este arquivo deve ser corrigido.

## Conceito: o caderno do professor

Papel branco sobre uma mesa clara, tinta azul, e uma caneta vermelha que só aparece para corrigir. Três ideias sustentam tudo:

1. **A página é o produto.** O que o professor imprime é a folha. A tela usa a mesma linguagem: papel, margem, linhas.
2. **O vermelho é caneta, não alarme.** Aparece apenas onde há correção de inglês. Nunca em botões, ícones ou erros do sistema
   (esses usam outro tom, ver Cor). Assim, vermelho na tela sempre significa "um aluno errou aqui, e esta é a forma certa".
3. **Corrigir é ensinar.** A correção é escrita acima do trecho, como o professor faria no caderno, em vez de ser sublinhada
   e punida.

O nome vem de *pauta*: as linhas do caderno e também o roteiro de uma aula.

## Marca

O símbolo é uma folha de caderno: três linhas pautadas e a margem vermelha à esquerda. A margem é a mesma linha que corta a
lateral de toda folha de atividades na interface, então o símbolo e o produto se reconhecem.

| Arquivo | Uso |
|---|---|
| [`marca-pauta.svg`](marca-pauta.svg) | Padrão, sobre fundo claro |
| [`marca-pauta-sobre-escuro.svg`](marca-pauta-sobre-escuro.svg) | Sobre a tinta azul (a barra superior do app) |
| [`marca-pauta-mono.svg`](marca-pauta-mono.svg) | Impressão em preto e branco, carimbo, fax. A margem vira pontilhado para não depender de cor |

**Assinatura (logotipo):** o símbolo seguido de "Pauta" em Bricolage Grotesque 700, caixa mista, espaçamento −0,02em,
com um espaço entre os dois igual a 0,35 da altura do símbolo.

**Área de respeito:** meia altura do símbolo em todos os lados. **Tamanho mínimo:** 16 px na tela, 6 mm no papel.

**Não faça:** esticar ou girar o símbolo; trocar o vermelho da margem por outra cor; colocar a margem à direita; escrever o
nome em caixa alta; pôr sombra, brilho ou gradiente; usar o vermelho do símbolo como cor de botão.

## Cor

Seis cores de base e uma regra de papel para cada uma.

| Nome | Valor | Papel |
|---|---|---|
| Tinta | `#1b2559` | Texto, títulos, botões principais, a barra superior |
| Papel | `#ffffff` | Folhas, cartões, campos |
| Mesa | `#e9eef4` | Fundo da página, atrás do papel |
| Caneta | `#c8243a` | **Só correção de erro de inglês** e a margem da folha |
| Marca-texto | `#ffe066` | Destaque de busca e tópicos a retomar |
| Acerto | `#1f7a4d` | Resposta certa, gabarito, ponto forte do aluno |

Apoio: tinta suave `#4a5380` (texto secundário), linha `#c9d6ea` e `#9fb3d6` (pautas e bordas), foco `#2f5bea`
(anel de foco), caneta suave `#fdeceb` (fundo de aviso de erro do sistema), acerto suave `#e4f4ec`.

**Falantes** (seis tons, sem vermelho): `#2f5bea`, `#0e7f86`, `#7b3fc4`, `#b25a00`, `#a82d78`, `#56751c`. A cor identifica a
pessoa na transcrição e nunca carrega sentido de certo ou errado.

**Erros do sistema** (envio falhou, servidor fora do ar) usam caneta suave de fundo e texto vermelho escuro `#8d1424`, dentro
de uma caixa. Não usam o vermelho de correção solto sobre o papel.

**Contraste medido (WCAG):** tinta sobre papel 14,4:1; tinta sobre mesa 12,4:1; tinta suave sobre papel 7,4:1; caneta sobre
papel 5,6:1; acerto sobre papel 5,3:1; texto escuro sobre caneta suave 8,1:1; tinta sobre marca-texto 11,1:1. Todos os seis tons
de falante passam de 4,5:1 sobre o papel. Não há tema escuro: o visual de papel depende do fundo claro.

## Tipografia

Duas famílias com funções bem diferentes.

- **Bricolage Grotesque 600/700** nos títulos, nas abas e na assinatura. Tem personalidade nas formas e entrelinha apertada.
- **Atkinson Hyperlegible Next 400/600/700** em todo o resto. Foi desenhada para distinguir letras parecidas, o que importa
  quando o aluno lê um enunciado em inglês numa folha impressa.

Ambas vêm do Google Fonts. Sem internet, caem para a fonte do sistema e a interface continua legível.

| Uso | Tamanho | Peso | Observação |
|---|---|---|---|
| Título de página | 30 px (24 em telas estreitas) | 700 | Bricolage, −0,015em |
| Título de seção | 22 px | 700 | Bricolage |
| Nome na folha | 24 px | 700 | Bricolage |
| Subtítulo dentro da folha | 17 px | 700 | Bricolage |
| Texto | 16 px, entrelinha 1,6 | 400 | Atkinson |
| Enunciado de atividade | 16 px | 600 | Atkinson |
| Nota e dica | 14 px | 400 | Atkinson, tinta suave |

Regras: texto sempre em caixa mista, sem caixa alta em rótulos; linhas de até 70 caracteres; números de tempo e de minutos com
`font-variant-numeric: tabular-nums`; não acentuar uma palavra isolada de um título com cor ou itálico.

## Forma e espaço

- Raios: 10 px nos cartões e folhas, 6 px em botões e campos, 999 px só em pílulas e interruptores.
- Sem sombras. A separação vem de bordas de 1 px na cor de linha, como papel sobre mesa.
- **A folha** (`.paper`): fundo branco, margem vermelha vertical a 46 px da esquerda, recuo interno de 64 px à esquerda.
  É o elemento mais característico e só aparece em material que o professor imprime ou revisa: folhas de aluno, gabarito, plano.
  Cartões de interface (formulário, pessoas, estados) ficam sem margem.
- Espaço entre blocos: 20 a 24 px. Conteúdo alinhado à esquerda; nada centralizado, exceto estados vazios e de carregamento.
- Em telas de até 640 px a margem vermelha some e a folha ocupa a largura toda, com 18 px de recuo.

## O elemento memorável: a correção em caneta vermelha

Na transcrição, cada erro de um aluno recebe um sublinhado ondulado vermelho e, **acima do trecho**, a forma correta em
vermelho pequeno (`<ruby>`). Passar o mouse mostra a explicação. É o único ponto da interface onde o vermelho vive solto, e
por isso a interface inteira pode ficar quieta ao redor.

Nas folhas, o mesmo gesto aparece como erro riscado em vermelho, seta, e a forma certa em verde, com a explicação em
português logo abaixo.

## Movimento

Quase nenhum. Só há movimento que responde a uma ação ou indica espera: o círculo de carregamento, o ponto pulsante de aula em
processamento, e a troca de aba. Nada de entradas deslizantes, nada de efeito ao passar o mouse em cartões.
`prefers-reduced-motion` desliga o que existe.

## Voz e texto

O professor é o usuário, e o texto fala com ele. Verbos simples, frases curtas, caixa mista. A interface é discreta, como
um bom colega de sala dos professores.

- **Nomes fixos:** *aula* (a gravação), *aluno*, *atividades*, *folha* (o que se imprime por aluno), *gabarito*,
  *plano da próxima aula*. Não alterne com "exercício", "ficha", "relatório" ou "job".
- **Ações dizem o que fazem:** "Transcrever a aula", "Criar atividades e plano", "Imprimir folha de Ana". Evite "Enviar" e "OK".
- **Mesma palavra no fluxo inteiro:** o botão "Criar atividades e plano" mostra "Criando o material…" e a aba ganha "pronto".
- **A IA nunca é apresentada como certa:** "A IA lê só o texto da transcrição, sem ouvir o áudio. Confira o material antes de
  entregar." Esse aviso aparece onde o professor decide gerar e onde revisa.
- **Vazio é convite:** "Nenhuma aula ainda. Envie a primeira gravação."
- **Erro explica e orienta, sem pedir desculpas:** "Formato não suportado: aula.txt. Use mp3, wav, mp4…"

| Em vez de | Escreva |
|---|---|
| Submit, Enviar | Transcrever a aula |
| Job concluído | Aula pronta |
| Erro 400 | Marque pelo menos um participante como aluno. |
| Gerar relatório de exercícios | Criar atividades e plano |

Os textos de ensino dentro do material (enunciados, opções, respostas) são em inglês. Explicações para o aluno e todo o resto
da interface são em português do Brasil.

## Impressão

O PDF sai do imprimir do navegador. Na impressão: tudo em preto sobre branco, sem a margem vermelha, sem cor de fundo, folha
do aluno sem respostas, uma folha por página, enunciados e itens de revisão sem quebra no meio. O título da janela vira o nome
sugerido do PDF ("Atividades, Ana, 22 de novembro de 2026").

## Acessibilidade

Anel de foco visível de 3 px azul em tudo que se clica; abas com setas do teclado; interruptores e opções com rótulo; sem
informação só por cor (o erro tem sublinhado e texto, o papel de cada pessoa tem rótulo); layout sem rolagem horizontal a
partir de 375 px; contraste mínimo 4,5:1.

## Alternativas descartadas

- **Painel escuro com roxo e gradiente** (a primeira interface do projeto): parece qualquer produto de análise de dados e não
  diz nada sobre aula.
- **Papel creme com serifa e terracota:** associa-se de imediato a documentos "gerados por IA".
- **Símbolo de lista com visto** (a primeira versão do ícone): lê-se como aplicativo de tarefas, e o visto transmite aprovação,
  quando a Pauta trata de correção. Foi trocado pela margem vermelha do caderno.
- **Fonte manuscrita para as correções:** aparência de brinquedo e legibilidade pior. A caneta vermelha é sugerida pela cor e
  pela posição acima do trecho.
- **Vermelho em botões e alertas:** diluiria o único uso com significado.

## Onde isto vive no código

| Item | Arquivo |
|---|---|
| Tokens, componentes, impressão | `telecom/web/static/styles.css` |
| Marca no cabeçalho e ícone da aba | `telecom/web/static/index.html` |
| Correção em ruby, folhas, plano | `telecom/web/static/app.js` |
| Textos de interface | `telecom/web/static/app.js` (em português, no próprio código) |
