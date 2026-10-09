# Transcrição Diarizada com Timestamps e Pydantic

- **Arquivo:** `Aula.wav`
- **Duração do Áudio:** `39.89 min` (2393.2s)
- **Tempo Total de Execução:** `141.366s` (2.36 min)
- **Tokens Utilizados:** `180967` (Entrada: `85311`, Saída: `47204`)
- **Custo Estimado:** `US$ 0.04112` (~ `R$ 0.2344`)
- **Total de Turnos de Fala:** `565`

---

**[00:00 - 00:02] Professor:**
> Maria 15 e 10, né?

**[00:02 - 00:03] Professor:**
> 15 e 10.

**[00:03 - 00:08] Professor:**
> Aqui é da 254 e apareceu um carry out aqui que corresponde a somar o quê?

**[00:08 - 00:10] Professor:**
> 256.

**[00:10 - 00:13] Professor:**
> A conta tá preservada, tá certo.

**[00:14 - 00:14] Professor:**
> Tá?

**[00:15 - 00:18] Professor:**
> Só olhando os sinais, diferente do overflow.

**[00:19 - 00:20] Professor:**
> Tá claro isso aí, gente?

**[00:25 - 00:29] Aluna:**
> A gente não tinha que subir quando o carry out

**[00:30 - 00:31] Professor:**
> Ah, boa pergunta.

**[00:32 - 00:33] Professor:**
> Vamos lá, boa pergunta dela.

**[00:35 - 00:39] Professor:**
> Como é que eu, né, como é que eu vou saber o que dá, o que não dá?

**[00:40 - 00:42] Professor:**
> Vamos imaginar agora uma unidade que soma e subtrai.

**[00:43 - 00:45] Professor:**
> Os números são inteiros sem sinal.

**[00:47 - 00:48] Professor:**
> Então vamos colocar aqui, ó.

**[00:50 - 00:54] Professor:**
> 255 aqui, que é o limite, finge que tem 8 bits.

**[00:55 - 00:56] Professor:**
> 255 aqui.

**[00:58 - 00:59] Professor:**
> Né?

**[01:30 - 01:30] Professor:**
> É?

**[01:32 - 01:32] Professor:**
> Vamos ver.

**[01:33 - 01:35] Professor:**
> Que que, que que, quanto vale isso aqui?

**[01:36 - 01:37] Professor:**
> Qual o resultado que deu aqui?

**[01:40 - 01:41] Aluna:**
> 254.

**[01:41 - 01:41] Professor:**
> 254.

**[01:43 - 01:45] Professor:**
> Só que o resultado é esse?

**[01:46 - 01:46] Professor:**
> Não.

**[01:51 - 02:01] Professor:**
> O resultado é 254 mais 20 de carry, não é isso? Que no caso é 1 x 256.

**[02:02 - 02:06] Professor:**
> O resultado, na verdade, é o quê? 250, 510.

**[02:08 - 02:09] Professor:**
> Bateu?

**[02:13 - 02:13] Professor:**
> Bateu?

**[02:16 - 02:17] Aluna:**
> Não, você, a, a, a

**[02:17 - 02:19] Professor:**
> Agora vamos fazer o contrário, vamos subtrair.

**[02:22 - 02:27] Professor:**
> Vamos subtrair o cara aqui. Vamos supor que é primeiro é menor do que o segundo, então.

**[02:28 - 02:38] Professor:**
> Vamos colocar aqui 1 menos 255.

**[02:40 - 02:41] Professor:**
> Ou 0 menos 255.

**[02:45 - 02:46] Professor:**
> Que que ficaria isso?

**[02:55 - 02:56] Professor:**
> Subtração isso aqui.

**[02:58 - 03:00] Professor:**
> Subtração disso aqui vai ser 0.

**[03:04 - 03:06] Professor:**
> 000.

**[03:07 - 03:09] Professor:**
> Não? Isso aqui vai ser um.

**[03:10 - 03:15] Professor:**
> Isso é para 000000.

**[03:18 - 03:22] Professor:**
> Só que eu sei o quê? Que aqui quem é o o carry out?

**[03:22 - 03:23] Professor:**
> Zero.

**[03:24 - 03:28] Professor:**
> Então se isso aqui é zero, o borrow é um.

**[03:29 - 03:31] Professor:**
> Então qual o resultado que deu aqui?

**[03:31 - 03:34] Professor:**
> 0 - 255, cuspiu aqui, ó.

**[03:36 - 03:36] Professor:**
> Um.

**[03:37 - 03:41] Professor:**
> Mas gerou o quê? Borrow igual a um.

**[03:43 - 03:48] Professor:**
> Se gerou borrow igual a um, o cara lá dentro somou 2 elevado a N.

**[03:48 - 03:52] Professor:**
> Então tem que pegar esse um e subtrair de 2 elevado a N.

**[03:54 - 03:58] Professor:**
> Em particular aqui é o quê? É 2 elevado a 8.

**[03:59 - 04:02] Professor:**
> Tá. Um que é mais 256.

**[04:03 - 04:06] Professor:**
> Então 255.

**[04:08 - 04:13] Professor:**
> Ah, mas lá dentro, esses sinais em termos de saída da caixa são diferentes.

**[04:14 - 04:18] Professor:**
> Mas lá dentro na caixa, esses sinais vêm da mesma origem.

**[04:19 - 04:22] Professor:**
> Quer dizer, no fundo, no fundo, se eu implementar esse cara aqui, qual?

**[04:22 - 04:29] Professor:**
> Um somador, eu vou pegar o carry out ligado direto, e vou pegar esse aqui e vou, ó, colocar o inversor aqui.

**[04:30 - 04:30] Professor:**
> É um lugar.

**[04:32 - 04:32] Professor:**
> Entendeu?

**[04:33 - 04:34] Professor:**
> Internamente a origem é a mesma.

**[04:35 - 04:39] Professor:**
> A maneira que ele é externado, analisado, é diferente.

**[04:41 - 04:43] Professor:**
> Eu tenho que olhar pro carry out e pro borrow quando eu tô subtraindo.

**[04:44 - 04:47] Professor:**
> Eu tenho que olhar, em resumo, eu tenho que olhar pro carry out quando eu tô somando.

**[04:49 - 04:51] Professor:**
> Que é o flag de estouro pra soma.

**[04:51 - 04:55] Professor:**
> E eu tenho que olhar pro pedido emprestado quando eu tô subtraindo.

**[04:57 - 05:00] Professor:**
> Ainda que lá dentro eles têm a mesma origem.

**[05:00 - 05:02] Professor:**
> Cuidado pra não confundir isso, a lógica dela é boa.

**[05:03 - 05:10] Professor:**
> Cuidado pra não confundir. Embora eles tenham a mesma origem, o sentido, o significado deles é diferente, como eu operacionalizo eles na minha conta é diferente.

**[05:11 - 05:11] Professor:**
> Tá?

**[05:14 - 05:15] Professor:**
> Beleza, gente?

**[05:17 - 05:19] Professor:**
> Juntar tudo num pagode só. Ó.

**[05:20 - 05:21] Professor:**
> Como é que é o pagode, ó.

**[05:23 - 05:25] Professor:**
> Aqui ele fez o quê? Vamos lá.

**[05:27 - 06:10] Professor:**
> Ele resolveu, ó, colocou a flag do overflow.

**[06:10 - 06:13] Professor:**
> Tá vendo? O overflow independe se é soma ou subtração.

**[06:14 - 06:19] Professor:**
> Na realidade, o overflow é mais pra trabalhar complemento a dois, entendeu?

**[06:22 - 06:25] Professor:**
> Porque, quando você trabalhar com números sem sinal, nunca vai dar overflow.

**[06:26 - 06:32] Professor:**
> Que a gente acabou de chegar à conclusão é o seguinte: se os números estiverem na faixa sem sinal, nunca dá overflow.

**[06:33 - 06:35] Professor:**
> O overflow só existe pra complemento a dois.

**[06:36 - 06:36] Professor:**
> Guarda isso.

**[06:38 - 06:40] Professor:**
> Né? Ó lá, overflow.

**[06:00 - 06:01] Professor:**
> uso exclusivo.

**[06:01 - 06:04] Professor:**
> com o nome adicional, complemento a dois.

**[06:05 - 06:07] Professor:**
> Não tem esse overflow se os números não tem sinal.

**[06:08 - 06:12] Professor:**
> A gente fez N contas aqui e não deu overflow.

**[06:13 - 06:16] Professor:**
> Esse caso aqui, ó, 255 mais 255.

**[06:17 - 06:20] Professor:**
> O o resultante cabe? Não cabe.

**[06:20 - 06:28] Professor:**
> Tanto que deu 254, mas você com a flag do do carry, você recupera o resultado.

**[06:30 - 06:42] Professor:**
> Então, ó, carry e borrow não são flags críticas no sentido de que a conta está errada. Overflow a conta tá errada, joga no lixo.

**[06:44 - 06:44] Professor:**
> Over

**[06:46 - 06:47] Professor:**
> Overflow.

**[06:47 - 06:48] Professor:**
> Perdão.

**[06:48 - 06:57] Professor:**
> Carry out e borrow são flags que dizem pra gente o quê? Ó, corrige o resultado em alguns casos. É só isso, basicamente, é isso.

**[06:57 - 07:05] Professor:**
> Ou seja, se tem um carry out, o que que ele tem que fazer? O resultado que a máquina me deu, eu tenho que somar 2 elevado a N.

**[07:06 - 07:15] Professor:**
> Se subtrair, deu borrow. Se o borrow, se tem borrow, eu tenho que subtrair 2 elevado a N do resultado.

**[07:15 - 07:16] Professor:**
> Só isso.

**[07:17 - 07:17] Professor:**
> Certo?

**[07:19 - 07:25] Professor:**
> O que ele fez aqui, ó, tô batendo nisso pra ver se isso entra como manta na sua cabeça, porque você nunca mais erra isso.

**[07:28 - 07:30] Professor:**
> Você fica perdido aqui, um monte de

**[07:30 - 07:30] Professor:**
> Acho.

**[07:32 - 07:33] Professor:**
> Bom.

**[07:33 - 07:42] Professor:**
> Ó, o cara que, ó, montando a estrutura interna com o complementador dois, ele é malandro, para não dar bode.

**[07:42 - 07:50] Professor:**
> Né? Então ele faz x + 1, x - y, manipula, senão faz essa manipulação com sinal, sem sinal, tudo certo.

**[07:50 - 07:52] Professor:**
> Excelente.

**[07:52 - 07:53] Professor:**
> Né?

**[07:53 - 08:11] Professor:**
> Lembrando uma coisa, quando a gente fez um detalhe, quando a gente fez aquela caixinha, que eu já apaguei a caixinha. Quando a gente fez aquele subtrator com caixinha, a gente fez um subtrator a rigor que era para números sem sinal.

**[08:12 - 08:18] Professor:**
> A gente só mostrou esse subtrator funcionando para números com sinal e complementador dois.

**[08:19 - 08:19] Professor:**
> Tá?

**[08:20 - 08:27] Professor:**
> Então, trabalhou com complementador dois, tem complementador dois na sua arquitetura, a solução vai ser o quê? Essa aqui.

**[08:28 - 08:31] Professor:**
> Eu nunca testei o outro com número complementador dois, provavelmente vai dar o quê? Errado.

**[08:32 - 08:32] Professor:**
> Tá?

**[08:35 - 08:42] Professor:**
> Então, ó, isso aqui, se eu for trabalhar, em outras palavras, se eu trabalho com números só inteiros e sem sinal.

**[08:42 - 08:44] Professor:**
> Eu posso usar aquelas duas arquiteturas.

**[08:45 - 08:55] Professor:**
> Posso usar essa e posso usar a das células somador, da propagação do borrow para subtração e da soma.

**[08:55 - 08:58] Professor:**
> Se eu for trabalhar com complementador dois, essa aqui.

**[08:58 - 08:59] Professor:**
> E

**[08:59 - 09:00] Professor:**
> Essa aqui.

**[09:00 - 09:04] Professor:**
> vou trabalhar, perdão, com números com sinal e sem sinal é essa que fica aqui. Default, padrão.

**[09:06 - 09:09] Professor:**
> Complementador de segundo e aí vem aqui, ó, o carry out.

**[09:10 - 09:13] Professor:**
> O carry out, né, ele vai

**[09:14 - 09:21] Professor:**
> Até interessante aqui, cadê? O carry out, ele, ah, o próprio sinal de soma ou subtração vai controlar o que tá saindo aqui.

**[09:22 - 09:27] Professor:**
> Ou vai sair o carry out ou vai sair o carry out barrado, porque ele quis botar no mesmo pino borrow.

**[09:28 - 09:31] Professor:**
> Mas se tivesse pino separado, ele se um pino, né, esse.

**[09:32 - 09:37] Professor:**
> Aqui, ó, eu tô escolhendo se esse carry out é carry out de fato ou se ele é borrow.

**[09:38 - 09:39] Professor:**
> Basicamente isso, tá?

**[09:40 - 09:42] Professor:**
> Então tá aqui o nosso somador e subtrator.

**[09:47 - 09:48] Professor:**
> E tá aqui explicando, ó.

**[09:50 - 09:59] Professor:**
> Overflow é só para complementador dois e o sentido da carry é eu poder saber o que fazer com o número sem sinal.

**[10:00 - 10:01] Professor:**
> Vou perguntar aí, né?

**[10:03 - 10:04] Professor:**
> Bom.

**[10:05 - 10:07] Professor:**
> Agora vamos lá. Eh,

**[10:08 - 10:14] Professor:**
> Que que acontece? A gente vai querer gravar esse resultado da última conta.

**[10:15 - 10:17] Professor:**
> Né? Por que que a gente vai querer gravar o resultado da última conta?

**[10:18 - 10:21] Professor:**
> Porque a gente vai pegar esse negócio, vai colocar numa máquina sequencial.

**[10:22 - 10:25] Professor:**
> E a cada, sei lá, segundo clock, a gente vai fazer uma operação diferente.

**[10:27 - 10:30] Professor:**
> Então é interessante que a gente guarde o status.

**[10:30 - 10:35] Professor:**
> né? Ou que a gente guarde o que que aconteceu na última operação feita.

**[10:37 - 10:38] Professor:**
> Então assim,

**[10:39 - 10:41] Professor:**
> Por exemplo, fiz uma conta aqui.

**[10:42 - 10:43] Professor:**
> Deu carry out.

**[10:44 - 10:51] Professor:**
> Se eu fiz uma conta, deu carry out, eu tenho que lembrar que eu vou ter que fazer, por exemplo, alguma correção no valor lido,

**[10:52 - 10:52] Professor:**
> né?

**[10:53 - 10:57] Professor:**
> Se eu tirei os números daqui, ó, acabou, vai ter outro resultado, vai ter outro carry out.

**[10:58 - 11:03] Professor:**
> Então, o que que a gente faz para armazenar os resultados dessas da carry out e do overflow?

**[11:04 - 11:15] Professor:**
> A gente alimenta os flip-flops, tá? E guarda no flip-flop do tipo D o último resultado, o último carry out e o último overflow da última operação feita.

**[11:16 - 11:16] Professor:**
> Tá?

**[11:17 - 11:21] Professor:**
> Isso a gente chama de flag. A gente chama esse de flag de status.

**[11:21 - 11:25] Professor:**
> Né? Então, status ou flag de status se refere ao quê?

**[11:27 - 12:14] Professor:**
> A a a situação da conta, a situação da conta da última conta feita.

**[12:17 - 12:19] Professor:**
> Deu carry out? Ele grava.

**[12:19 - 12:21] Professor:**
> Deu overflow? Ele grava.

**[12:21 - 12:29] Professor:**
> E vai ter para outras coisas, vai ter uma flag para sinal, por exemplo, o resultado da última operação foi positivo ou negativo? Vai ter a flag de sinal.

**[12:30 - 12:30] Professor:**
> Tá?

**[12:31 - 12:38] Professor:**
> O resultado da última operação foi igual a zero ou foi diferente de zero? Vai ter uma flag de zero também.

**[12:38 - 12:39] Professor:**
> Tá?

**[12:00 - 12:03] Professor:**
> E aí, dando spoiler, a gente vai usar isso aonde?

**[12:03 - 12:06] Professor:**
> Quando a gente começar a construir algoritmos.

**[12:06 - 12:09] Professor:**
> Você vai fazer um if. Se A maior do que B.

**[12:10 - 12:13] Professor:**
> Se A maior que B faz isso, se A menor que B faz aquilo.

**[12:13 - 12:16] Professor:**
> Você vai olhar o quê? A flag de sinal.

**[12:17 - 12:20] Professor:**
> Você vai fazer a conta e vai olhar a flag de sinal. E assim vai.

**[12:20 - 12:22] Professor:**
> Tá? Beleza até aí? Tá claro?

**[12:24 - 12:25] Professor:**
> Não, mudou nada.

**[12:25 - 12:26] Professor:**
> O que que a gente fez?

**[12:27 - 12:29] Professor:**
> Pegou a saída da caixa, ligou nos flip-flops, ponto.

**[12:30 - 12:37] Professor:**
> Esse flip-flop vai ser colocado aqui, controlado, vai ter um enable lá que a gente vai gerenciar depois, tá?

**[12:41 - 12:45] Professor:**
> Olha mostrando aqui, ó, essas contas, né, no computador.

**[12:46 - 12:49] Professor:**
> Que que é isso aqui? É grego, aramaico, alemão?

**[12:50 - 12:51] Professor:**
> Quase isso.

**[12:51 - 12:52] Professor:**
> Que que ele fez, ó?

**[12:53 - 12:56] Professor:**
> Ele pegou números.

**[12:56 - 12:59] Professor:**
> Bom, vamos lá, você entendeu um pouquinho disso agora.

**[13:40 - 13:42] Professor:**
> Você nunca viu esse troço, mas preto e branco.

**[13:42 - 13:43] Professor:**
> Vamos lá, é...

**[13:47 - 13:52] Professor:**
> No seu computador, você tem o tal do processador, que é o chip central que faz tudo.

**[13:53 - 13:57] Professor:**
> Tá? E ele, vamos dizer assim, ele responde a instruções.

**[13:58 - 14:00] Professor:**
> Então você dá uma instrução e ele...

**[14:02 - 14:10] Professor:**
> Aqui, então, ele pegou lá no computador, um ambiente aí que vocês vão ver depois, e mandou o quê? Subtrair esse A L do B.

**[13:30 - 13:33] Professor:**
> Quem são esses AL e BH?

**[13:33 - 13:40] Professor:**
> Quando você manda esse cara fazer uma conta, você tem que guardar os números em algum lugar. Esse algum lugar se chama registrador.

**[13:41 - 13:49] Professor:**
> O registrador é um grande flip-flop, na verdade é um conjunto de flip-flops que vai ter um determinado tamanho, né?

**[13:50 - 13:58] Professor:**
> Aqui, por exemplo, ó, esse AL aqui, ele tem 16 bits.

**[13:58 - 14:02] Professor:**
> É como se fosse, sei lá, você tem um AL ou um AH.

**[14:02 - 14:11] Professor:**
> O AL é a parte baixa, né, do do do A. E o AH é a parte alta do A.

**[14:12 - 14:15] Professor:**
> Por que AL AH? Porque de onde vem essa idiotice?

**[14:16 - 14:21] Professor:**
> Quando o cara inventou esse processador, essa arquitetura, ela vem lá do 8080.

**[14:22 - 14:29] Professor:**
> Né? Que é o que é o sucessor do 4004, o primeiro processador. O primeiro processador tinha 4 bits.

**[14:29 - 15:12] Professor:**
> O segundo tinha 8. Esse tinha 16.

**[15:13 - 15:20] Professor:**
> Então ele pegou o A, que era o registrador de para fazer conta, e duplicou o número de bits.

**[15:21 - 15:25] Professor:**
> Mas para poder se referenciar aos dois pedaços, ele colocou parte baixa e parte alta.

**[15:25 - 15:26] Professor:**
> Tá tranquilo até aí?

**[15:28 - 15:29] Professor:**
> Então

**[15:29 - 15:31] Aluna:**
> Oi? Parte baixa, parte alta.

**[15:31 - 15:34] Professor:**
> Imagina o seguinte aqui, ó. É uma palavra, você comum.

**[15:35 - 15:37] Professor:**
> Normalmente a gente pensa em palavras em bytes.

**[15:38 - 15:40] Professor:**
> Ah, então aqui, por exemplo, o A

**[15:00 - 15:03] Professor:**
> de interior. O A0 até o A7.

**[15:03 - 15:06] Professor:**
> o A8 até o A15.

**[15:06 - 15:08] Professor:**
> Esse seria o o A.

**[15:09 - 15:12] Professor:**
> chamar AX.

**[15:13 - 15:13] Professor:**
> Tá?

**[15:14 - 15:20] Professor:**
> Esse AX tem uma parte baixa, bits menos significativos e uma parte alta.

**[15:21 - 15:21] Professor:**
> Tá?

**[15:23 - 15:24] Professor:**
> Ah, e o EAX?

**[15:26 - 15:27] Professor:**
> O EAX é o

**[15:28 - 15:29] Professor:**
> É isso aqui com 32.

**[15:30 - 15:30] Professor:**
> Tá?

**[15:31 - 15:35] Professor:**
> Mas isso aqui a gente, isso aqui só vai a partir do 386.

**[15:36 - 15:37] Professor:**
> Esquece, por enquanto.

**[15:38 - 15:38] Professor:**
> Tá?

**[15:40 - 15:44] Professor:**
> O seu, o seu tem 64, 64.

**[15:45 - 15:45] Professor:**
> Tá?

**[15:46 - 15:50] Professor:**
> Mas então, vamos lá. Aí o que que esse, como é que esse cara mais ou menos é, pra vocês terem uma noção?

**[15:50 - 15:55] Professor:**
> Não vou ficar entrando muito nisso, isso é mais pro final e isso é uma arquitetura mais específica.

**[15:57 - 16:01] Professor:**
> Esse, cada um desses registradores aqui, você pode ver, ó,

**[16:02 - 16:04] Professor:**
> Ah, olha que coisa legal aqui, ó.

**[16:05 - 16:07] Professor:**
> Como é que eu sei que esse cara tem 16 bits, gente?

**[16:11 - 16:13] Professor:**
> Eu falei que tem 16, você acreditou, mas como é que eu sei?

**[16:13 - 16:16] Professor:**
> Ali tá escrito ali, tem 16.

**[16:16 - 16:18] Aluna:**
> A quantidade de bits disponíveis ali tá de

**[16:18 - 16:18] Professor:**
> O que o quê?

**[16:19 - 16:21] Aluna:**
> A quantidade de bits disponíveis ali pra você anotar tá

**[16:23 - 16:23] Aluna:**
> 24.

**[16:24 - 16:25] Professor:**
> Por que que é 4?

**[16:27 - 16:28] Professor:**
> Você ia falar, vai.

**[16:29 - 16:29] Professor:**
> Você ia falar.

**[16:30 - 16:30] Aluna:**
> Hum?

**[16:31 - 16:33] Professor:**
> Você vai falar porque que tem 16.

**[16:34 - 16:38] Professor:**
> Quatro algarismos.

**[16:38 - 16:42] Professor:**
> Quatro algarismos em hexa, o conteúdo deles são quatro algarismos em hexa.

**[16:42 - 16:45] Professor:**
> Cada algarismo, algarismo em hexa leva quantos bits?

**[16:46 - 16:47] Aluna:**
> Quatro.

**[16:47 - 16:48] Professor:**
> Quatro.

**[16:48 - 16:50] Professor:**
> Então, ó, 4 4 4 4.

**[16:51 - 16:52] Aluna:**
> 16.

**[16:52 - 16:52] Professor:**
> 16.

**[16:53 - 16:56] Professor:**
> Então, pelo, pela palavra que eu te dei, você sabe o tamanho do registrador.

**[16:57 - 16:59] Aluna:**
> Beleza, grego.

**[16:59 - 17:01] Professor:**
> Beleza, grego. Eu falei grego.

**[17:06 - 17:07] Professor:**
> Vamos lá.

**[17:09 - 17:16] Professor:**
> Suponha que eu tenho uma caixa lá, um registrador low, que eu não sei o tamanho, e eu venho aqui e escrevo nele.

**[17:17 - 17:19] Professor:**
> 0x é só para dizer que tá em hexa, tá?

**[17:19 - 17:22] Professor:**
> A B C D E.

**[17:22 - 17:24] Professor:**
> Quantos bits tem esse registrador?

**[17:27 - 18:10] Professor:**
> Em hexa, para cada algarismo, eu preciso de quantos bits?

**[18:10 - 18:11] Aluna:**
> 20 bits.

**[18:12 - 18:12] Professor:**
> Quatro.

**[18:13 - 18:15] Professor:**
> Esse cara tem 20 bits.

**[18:20 - 18:20] Professor:**
> Tá?

**[18:24 - 18:24] Professor:**
> Então, ó.

**[18:26 - 18:31] Professor:**
> Esse cara tem esses registradores aqui, ó, AX, BX, CX, DX e outro.

**[18:32 - 18:32] Professor:**
> Tá?

**[18:32 - 18:36] Professor:**
> Cada um tem um papel, não vou ficar explicando aqui, que é papel de cada um.

**[18:37 - 18:40] Professor:**
> Ele ainda tem uma idiotice. Qual a idiotice dele?

**[18:00 - 18:05] Professor:**
> Você faz a conta e a conta sempre volta para o AX.

**[18:06 - 18:09] Professor:**
> Então, todas as contas que esse malandro faz são assim.

**[18:09 - 18:18] Professor:**
> AX recebe AX mais algum, mais, menos, dividido, multiplicado, qualquer outro registrador.

**[18:19 - 18:20] Professor:**
> Tá?

**[18:21 - 18:24] Professor:**
> Isso é o que a gente chama de arquitetura orientada a acumulador.

**[18:25 - 18:27] Professor:**
> Toda conta volta para o A.

**[18:29 - 18:30] Professor:**
> Por que esse pesadelo?

**[18:30 - 18:31] Professor:**
> Você história.

**[18:32 - 18:38] Professor:**
> Tá? Essa arquitetura é de 1970, é, é retrocompatível com um negócio de 1974.

**[18:39 - 18:45] Professor:**
> Tinha uma série de restrições na época em termos de, de hardware, que faziam o cara fazer isso.

**[18:45 - 18:48] Professor:**
> Isso aqui é para economizar porta, para economizar hardware.

**[18:49 - 18:51] Professor:**
> José Artur, ao extremo.

**[18:51 - 18:53] Professor:**
> Hoje não é mais feito assim.

**[18:53 - 18:55] Professor:**
> Graças ao Santo Bom Deus.

**[18:55 - 18:56] Professor:**
> Tá?

**[18:57 - 19:41] Professor:**
> Então vamos lá, ele colocou A e 8F no registrador.

**[19:01 - 19:08] Professor:**
> E tá fazendo uma conta, ó, subtrai a parte baixa do AL, da parte, da parte baixa do BL.

**[19:09 - 19:12] Professor:**
> Então, ó, ele tá fazendo com o AX aqui, botou um BX aqui.

**[19:13 - 19:15] Professor:**
> Tem outro BX aqui em cima.

**[19:16 - 19:19] Professor:**
> Esse BX tem um B low e tem um B high.

**[19:20 - 19:22] Professor:**
> Ele tá fazendo a conta entre essas duas partes aqui.

**[19:23 - 19:23] Professor:**
> Ok?

**[19:25 - 19:29] Aluna:**
> Então, se eu tivesse, se o BX fosse A08F, o A0 não ia fazer a...

**[19:29 - 19:30] Professor:**
> Não é fazer.

**[19:30 - 19:32] Professor:**
> Se o senhor quer BX, faz o quê?

**[19:32 - 19:33] Aluna:**
> A08F.

**[19:33 - 19:34] Professor:**
> A0.

**[19:34 - 19:35] Aluna:**
> A0 não ia fazer nada.

**[19:35 - 19:36] Professor:**
> A0 não ia fazer nada. Boa.

**[19:37 - 19:38] Professor:**
> Pergunta dela aqui, ó.

**[19:39 - 19:41] Professor:**
> Os números que ele colocou, vamos botar os números aqui, ó.

**[19:42 - 19:47] Professor:**
> No caso do AX, OK, aqui é 00, aqui é 0A.

**[19:48 - 19:48] Professor:**
> Entendeu?

**[19:49 - 19:55] Professor:**
> No caso do BX, ah, ele foi legal também, botou 00 e botou 8F aqui, né?

**[19:57 - 19:59] Professor:**
> Mas se eu coloco qualquer outra coisa aqui.

**[20:00 - 20:02] Professor:**
> Se eu botar FF aqui, FF aqui.

**[20:04 - 20:05] Professor:**
> O cara ignora, tá nem aí.

**[20:05 - 20:07] Professor:**
> Você mandou ele fazer a conta o quê?

**[20:09 - 20:09] Professor:**
> Isso aqui.

**[20:11 - 20:12] Professor:**
> Então, onde ele vai olhar?

**[20:13 - 20:14] Professor:**
> Tá?

**[20:14 - 20:18] Aluna:**
> Mas isso é um pedaço, é um pedaço da informação que tá naquele registrador.

**[20:20 - 20:22] Aluna:**
> Você vai querer só um pedaço da conta de um pedaço.

**[20:23 - 20:23] Professor:**
> Boa.

**[20:24 - 20:25] Professor:**
> Retrocompatibilidade.

**[20:26 - 20:27] Professor:**
> O que que ele queria?

**[20:27 - 21:10] Professor:**
> Quando ele lançou a versão de 8 bits do processador,

**[21:14 - 21:15] Professor:**
> só fazia em cima dessa parte.

**[21:16 - 21:17] Professor:**
> Nem existia.

**[21:18 - 21:21] Professor:**
> Aí ele expandiu, na versão 2.0, ele expandiu.

**[21:22 - 21:26] Professor:**
> Só que ele queria que o código do antigo rodasse, o código do novo rodasse no antigo.

**[21:26 - 21:27] Aluna:**
> Resposta é tão preguiça.

**[21:28 - 21:31] Professor:**
> Não, é mais importante do que isso.

**[21:32 - 21:34] Professor:**
> Ele queria que o código do antigo rodasse no novo.

**[21:35 - 21:38] Professor:**
> Então, ou seja, ó, o código do antigo rodar no novo,

**[21:38 - 21:40] Professor:**
> que que eu tenho que fazer? Primeiro,

**[21:00 - 21:08] Professor:**
> a a a representação, a gente vai ver depois, a representação da ordem em bits, que a gente chama de palavra de instrução, tem que ser a mesma.

**[21:09 - 21:11] Professor:**
> Ele manteve a palavra de instrução.

**[21:12 - 21:13] Professor:**
> Ele manteve a mesma estrutura do antigo.

**[21:14 - 21:16] Professor:**
> Mas aí ele deu liberdade para que usasse o novo.

**[21:18 - 21:18] Professor:**
> Entendeu?

**[21:19 - 21:23] Professor:**
> E com isso, você só tem um PC em cima da mesa por causa disso, sabia?

**[21:25 - 21:28] Professor:**
> Que um era compatível com o outro, que era compatível com o outro.

**[21:28 - 21:35] Professor:**
> Se você muda a arquitetura e quebra a retrocompatibilidade, você tem que reescrever o software todinho.

**[21:36 - 21:39] Professor:**
> E a gente estava numa época que reescrever software não era trivial.

**[21:41 - 21:44] Professor:**
> Então a Intel meio que ganhou o mercado também por causa disso.

**[21:44 - 21:48] Professor:**
> Você pega um código de 40 anos atrás, você roda aqui.

**[21:50 - 21:54] Professor:**
> Você roda o mesmo código de 40, 50 anos atrás, você roda no seu computador.

**[21:54 - 21:55] Aluna:**
> Ainda?

**[21:55 - 21:56] Professor:**
> Ainda.

**[21:57 - 21:57] Professor:**
> Roda.

**[21:58 - 22:05] Professor:**
> A menos que você faça as grandes paradas de acesso à memória, que o sistema vai dar erro de proteção, não sei o que, mas a grosso modo você roda o mesmo código.

**[22:06 - 22:06] Professor:**
> Tá?

**[22:08 - 22:09] Professor:**
> Essa é a graça disso aqui.

**[22:09 - 22:11] Professor:**
> Isso aqui roda código de 50 anos atrás.

**[22:12 - 22:14] Professor:**
> Nem nem faz mais sentido.

**[22:15 - 22:16] Professor:**
> E roda umas coisas.

**[22:17 - 22:19] Professor:**
> Só que ele roda mal esse código.

**[22:19 - 22:25] Professor:**
> Então o que é que as pessoas fazem? Quando elas escrevem softwares novos, elas tiram essas operações antigas, que não fazia sentido.

**[22:26 - 22:27] Professor:**
> Mas você roda.

**[22:28 - 22:30] Professor:**
> Se você pegar o Windows,

**[22:30 - 22:32] Professor:**
> Ó, vou pegar um exemplo besta.

**[22:32 - 22:36] Professor:**
> Você pega um Windows, XP.

**[22:37 - 22:41] Professor:**
> Não, XP é bom. Pega um Windows 95, um Windows 311.

**[22:42 - 22:44] Professor:**
> Se você pegar um Windows 311, você enfia ele aqui.

**[22:45 - 22:46] Professor:**
> No computador de hoje.

**[22:47 - 22:49] Professor:**
> 1990, pô.

**[22:50 - 22:51] Professor:**
> Tá? Por quê? Por causa da disso.

**[22:51 - 22:58] Professor:**
> E o Windows 311 trabalhava com 16. O teu hoje trabalha com 64, só para você ter uma noção de tamanho, tá?

**[23:01 - 23:01] Professor:**
> Isso é legal.

**[23:03 - 23:04] Professor:**
> Isso é o segredo da indústria.

**[23:05 - 23:13] Professor:**
> Né? O que você, né? O que os caras mais quer? Comprei PlayStation 5, quero rodar o jogo do PlayStation 4, do 3, do 2, etc e tal.

**[23:14 - 23:15] Professor:**
> E aí o cara não pode inventar muito.

**[23:16 - 23:16] Professor:**
> Tá?

**[23:20 - 23:21] Professor:**
> Bom, vamos lá. Para não empolgar muito.

**[23:22 - 23:24] Professor:**
> Então, se eu não empolgo aqui dá ruim.

**[23:25 - 23:27] Professor:**
> Vamos lá, supondo números inteiros sem sinal.

**[23:28 - 23:37] Professor:**
> Então, eu tinha esses valores aí, e quando eu botei esses valores aí, eu era um ser consciente.

**[23:38 - 23:43] Professor:**
> E coloquei eles certos, considerando eles inteiros sem sinal. Como esses caras são inteiros sem sinal,

**[23:43 - 23:47] Professor:**
> a representação do, do, do A. O A é 10, né?

**[23:47 - 23:49] Professor:**
> Isso aqui não é, não é, não é 10?

**[23:50 - 23:50] Aluna:**
> É.

**[23:51 - 23:52] Professor:**
> Logo, você zera o A.

**[23:52 - 23:53] Professor:**
> Para de chutar.

**[24:18 - 24:24] Professor:**
> Então, a representação do A e o outro, ó, 8F. 8F.

**[24:24 - 24:25] Professor:**
> Beleza?

**[24:26 - 24:27] Professor:**
> Tá tranquilo aí?

**[24:28 - 24:28] Professor:**
> Bit a bit?

**[24:30 - 24:31] Professor:**
> Vou pegar isso aqui e vou converter. Bom,

**[24:31 - 24:34] Professor:**
> isso aqui tá, tá em hexa, você coloquei em binário,

**[24:36 - 24:36] Professor:**
> né?

**[24:38 - 24:42] Professor:**
> E converti de binário para decimal. Então, você é 10 mais 143.

**[24:43 - 24:44] Professor:**
> Vou fazer um menos o outro.

**[24:46 - 24:50] Professor:**
> Um menos o outro. 10 menos 143 é menos 133.

**[24:51 - 24:51] Professor:**
> Certo?

**[24:51 - 24:52] Professor:**
> Vou fazer aquela ideia, ó.

**[24:53 - 24:57] Professor:**
> Vou pegar o primeiro, complemento a dois do segundo e somar um.

**[24:58 - 24:58] Professor:**
> Fazer aqui.

**[25:01 - 25:02] Professor:**
> Você já fez 300, né?

**[25:04 - 25:05] Professor:**
> Tira.

**[25:07 - 25:10] Professor:**
> Somar um. O resultado disso aqui é o quê? 7B.

**[25:11 - 25:12] Professor:**
> Deu isso aqui.

**[25:13 - 25:14] Professor:**
> O resultado deu isso aqui,

**[25:15 - 25:16] Professor:**
> né?

**[25:16 - 25:18] Professor:**
> 7B é 123.

**[25:18 - 25:20] Professor:**
> Esse é o resultado que apareceu, 123.

**[25:21 - 25:24] Professor:**
> Convertendo 123 para hexa,

**[25:25 - 25:26] Professor:**
> é BO.

**[25:26 - 25:30] Professor:**
> Então, se eu for olhar aqui o resultado aqui, ó, ah, cadê?

**[25:33 - 25:33] Professor:**
> B horas.

**[25:35 - 25:36] Professor:**
> Isso. Só.

**[25:36 - 25:39] Professor:**
> B horas, B0, B0, tô maluco. B0.

**[25:40 - 25:41] Professor:**
> Cadê o B0 na criança aqui? Espera aí.

**[25:42 - 25:45] Professor:**
> Pra, pra, pra, pra, pra.

**[25:49 - 25:49] Professor:**
> Aí, perdão, peraí.

**[25:51 - 25:51] Professor:**
> Não, falei besteira.

**[25:52 - 25:54] Professor:**
> O resultado é 7B, né?

**[25:55 - 25:56] Professor:**
> O resultado é 7B.

**[25:57 - 26:03] Professor:**
> Eu vou lá na saída do cara, após a realização da operação, e cheguei à conclusão que dá 7B, deu 7B.

**[26:04 - 26:04] Professor:**
> Tá batendo.

**[26:06 - 26:06] Professor:**
> Né?

**[26:06 - 26:09] Professor:**
> Agora vem a questão da da interpretação, né?

**[26:10 - 26:13] Professor:**
> Se o número era inteiro sem sinal, né?

**[26:13 - 26:18] Professor:**
> 7B é 200.

**[26:18 - 26:21] Professor:**
> 7B, na verdade, é quem?

**[26:22 - 26:23] Professor:**
> É, cadê?

**[26:25 - 26:27] Professor:**
> Vamos lá, 7B é.

**[26:30 - 26:35] Professor:**
> 255, 128, 128 menos.

**[26:35 - 26:38] Professor:**
> É, 128 menos 4.

**[26:40 - 26:41] Professor:**
> 123.

**[26:41 - 26:43] Professor:**
> Isso aí, 123.

**[26:44 - 26:49] Professor:**
> Bom, esse número aqui, né, se eu pensasse nele em complemento a dois, ele é 123.

**[26:50 - 26:52] Professor:**
> Esse número é 123, né?

**[26:55 - 26:56] Professor:**
> Aí o que que eu vou observar?

**[26:56 - 27:00] Professor:**
> Bom, ele tem uma flag aqui, ó, que disse assim, ó, pra ir de quebra.

**[27:00 - 27:04] Professor:**
> carry. Ele tá sinalizando uma flag de carry aqui pra gente.

**[27:05 - 27:10] Professor:**
> Se ele sinalizou uma flag de carry, a gente lembra que o carry deu igual a um, né?

**[27:12 - 27:16] Professor:**
> Espera aí. Então, se y o quê? Espera aí.

**[27:22 - 27:24] Professor:**
> É só borrow out, tem que ser o complemento do subtraendo.

**[27:30 - 27:34] Aluna:**
> Quando é soma, C é quando é carry, quando é subtração, C é igual a um.

**[27:35 - 27:40] Professor:**
> Não, tudo bem. Mas ele deu um, né? Tem que dar zero, né, pra pedir emprestado. Eu tenho que pedir emprestado.

**[27:41 - 27:45] Aluna:**
> Não, mas aí eu acho que ele já converteu. Ele já fez o note do carry.

**[27:46 - 27:51] Professor:**
> Ah, é verdade. É isso. Tem razão. Da maneira como ele representa, exato.

**[27:53 - 28:01] Professor:**
> Então, ó, aqui, né, ele disse o seguinte, ó, CY aqui significa que ele teve, ele fez a subtração e deu a flag de borrow aqui, direto.

**[28:02 - 28:09] Professor:**
> Eu pedi emprestado. Logo, esse número aqui, né, 123, ele está somado de 256.

**[28:10 - 28:13] Professor:**
> Logo, eu tenho que subtrair 256 para dar o resultado 133.

**[28:16 - 28:28] Professor:**
> Então, ó, não é esse resultado aqui que seria 123. Ele tem que olhar esse cara aqui para saber que esse resultado deu negativo e adaptar o valor para saber o valor certo.

**[28:29 - 28:30] Professor:**
> Agora, com números que tivessem sinal.

**[28:30 - 28:30] Professor:**
> sinal.

**[28:31 - 28:35] Professor:**
> Se o número tem sinal, os mesmos números aqui já tem um valor diferente.

**[28:35 - 28:37] Professor:**
> Primeiro continua com 10, obviamente.

**[28:38 - 28:46] Professor:**
> Mas o segundo, ó, vai virar o quê? Tem que pegar, eu vejo que esse bit mais significativo é um, então fazer o complemento a dois do que restou.

**[28:47 - 28:52] Professor:**
> 01, somar um, isso aqui vai dar menos 143.

**[28:54 - 28:56] Professor:**
> Olha, isso aqui vai dar quanto? Vai dar menos, deixa eu ver.

**[28:57 - 28:58] Professor:**
> 1 0

**[29:00 - 29:05] Professor:**
> 64 32 com 16, mais um.

**[29:08 - 29:08] Aluna:**
> 63.

**[29:11 - 29:12] Professor:**
> Vai dar 143.

**[29:12 - 29:13] Professor:**
> Beleza.

**[29:14 - 29:15] Professor:**
> Esse 143, então.

**[29:16 - 29:16] Professor:**
> Beleza?

**[29:19 - 29:25] Professor:**
> Esse 143 somados com o o 10, vão dar 153.

**[29:26 - 29:28] Professor:**
> Daria 153.

**[29:28 - 29:30] Professor:**
> Cadê? Peraí, peraí, peraí, peraí.

**[30:14 - 30:15] Professor:**
> Não, tá certo.

**[30:16 - 30:17] Professor:**
> Tinha um número lá.

**[30:17 - 30:18] Professor:**
> Isso, tem que fazer com.

**[30:19 - 30:20] Professor:**
> Isso, isso aqui é 143.

**[30:22 - 30:22] Professor:**
> Não, peraí.

**[30:24 - 30:25] Professor:**
> Tô fazendo.

**[30:25 - 30:27] Professor:**
> Não, isso aqui não é 143, isso aqui é 63.

**[30:29 - 30:32] Aluna:**
> 143 já é o 143 é o valor de cara, né?

**[30:33 - 30:35] Professor:**
> 6, 12, 3, vai.

**[30:39 - 30:40] Professor:**
> Ah,

**[30:00 - 30:02] Professor:**
> 7 10 113.

**[30:04 - 30:07] Professor:**
> Então esse aqui é o -113, tá ali.

**[30:07 - 30:09] Professor:**
> Jesus, o slide dele é um pouquinho confuso.

**[30:10 - 30:11] Professor:**
> Né?

**[30:12 - 30:14] Professor:**
> Então esse cara é esse menos esse.

**[30:15 - 30:16] Professor:**
> Esse número tá lá.

**[30:16 - 30:17] Professor:**
> Vai dar os 123.

**[30:18 - 30:19] Professor:**
> Né?

**[30:19 - 30:22] Professor:**
> O, o, o número resultante é o mesmo, ó, deu o mesmo 7B.

**[30:24 - 30:24] Professor:**
> Né?

**[30:25 - 30:26] Professor:**
> Fiz a subtração.

**[30:27 - 30:29] Professor:**
> Só que é um número inteiro com sinal.

**[30:29 - 30:30] Professor:**
> Não vou olhar o carry.

**[30:30 - 30:31] Professor:**
> Não vou olhar o borrow.

**[30:32 - 30:33] Professor:**
> Vou olhar o carry.

**[30:34 - 30:34] Professor:**
> Né?

**[30:37 - 30:38] Professor:**
> Esse carry aqui deu zero.

**[30:39 - 30:42] Professor:**
> Esse carry deu zero, então significa que esse número não precisa de ajuste.

**[30:43 - 30:47] Professor:**
> Então, de fato, ele é mais, isso aqui é 123, ele é mais 123.

**[30:49 - 31:42] Professor:**
> Então, deu o mesmo resultado, ó, só que as interpretações, o que, são completamente diferentes, a depender de quê? A depender da anotação dos números que eu armazenei originalmente.

**[31:43 - 31:43] Aluna:**
> Pode explicar de novo?

**[31:44 - 31:44] Professor:**
> Qual?

**[31:45 - 31:46] Professor:**
> Esse último aqui?

**[31:46 - 31:46] Aluna:**
> É.

**[31:47 - 31:48] Professor:**
> Então, vamos lá.

**[31:48 - 31:50] Professor:**
> Fiz um menos o outro, tem complemento a dois.

**[31:50 - 31:51] Aluna:**
> Sim.

**[31:51 - 32:00] Professor:**
> Então, vou ter que subir, pegar o segundo e transformar ele o quê? Ele era, vou ter que fazer o complementador dele de novo, independente do valor que ele esteja ali.

**[32:01 - 32:01] Aluna:**
> Bom.

**[32:02 - 32:05] Professor:**
> Esse cara já está em, vamos, vamos supor, esse cara já está em complementador dois.

**[32:06 - 32:10] Professor:**
> Ele em complementador dois é aqui, cadê? Esse cara aqui.

**[31:31 - 31:33] Aluna:**
> Enfim, aí tem que fazer o complementador em cima disso.

**[31:34 - 31:34] Professor:**
> Isso.

**[31:35 - 31:39] Professor:**
> Esse complementador em cima disso deu 143, né? Espera aí.

**[31:40 - 31:42] Professor:**
> Vamos lá. Como vocês fazem isso?

**[31:42 - 31:43] Aluna:**
> É um monte de operação que tem.

**[31:52 - 31:55] Professor:**
> Então, vamos lá. Vamos lá, pegar os números originalmente, acho que é complementador.

**[31:56 - 32:02] Professor:**
> Esse cara aqui era 00. Esse aqui é o 0.

**[32:04 - 32:10] Professor:**
> Esse cara é 1 0 0 0 1 1 1.

**[32:11 - 32:13] Professor:**
> Então esse cara aqui quem é?

**[32:14 - 32:19] Professor:**
> 128 mais 15.

**[32:20 - 32:21] Aluna:**
> É, eu tô fazendo ali.

**[32:24 - 32:27] Professor:**
> Vai dar três, vai um, 143.

**[32:27 - 33:10] Professor:**
> Esse cara, a rigor,

**[32:31 - 32:36] Professor:**
> Ah, não, desculpa. Esse cara tá em complementador dois. Vai com o sinal.

**[32:37 - 32:41] Professor:**
> Então esse cara, na verdade, é quem?

**[32:42 - 32:54] Professor:**
> Esse cara, na verdade, era 0 1 1 1 0 0 0 0 1 1 0 0 0 1 1 1 0.

**[32:55 - 32:59] Professor:**
> E esse número aqui é esse aqui que eu fiz a conta.

**[32:59 - 33:00] Professor:**
> 130.

**[33:00 - 33:00] Professor:**
> creio.

**[33:01 - 33:06] Professor:**
> Logo, esse número aqui era menos 100 e 13.

**[33:08 - 33:08] Professor:**
> Beleza?

**[33:10 - 33:12] Professor:**
> Aí o que que eu, eu pedi pra máquina fazer?

**[34:30 - 34:35] Professor:**
> 0 0 0 1

**[34:35 - 34:40] Professor:**
> 0 1 0 1 0

**[36:04 - 36:06] Aluna:**
> É porque que eu tenho que inserir na segunda parcela disso?

**[36:06 - 36:07] Professor:**
> Não, não, não, não.

**[36:07 - 36:08] Aluna:**
> É o outro, né?

**[36:08 - 36:08] Professor:**
> Oi?

**[36:08 - 36:09] Aluna:**
> É o outro, né?

**[36:09 - 36:10] Professor:**
> Pega do outro segmento.

**[36:11 - 36:13] Aluna:**
> Exato. Esse que eu tô com medo grande.

**[36:15 - 36:16] Professor:**
> Você vai pegar daqui direto.

**[36:16 - 36:18] Aluna:**
> Aqui é o máximo.

**[36:19 - 36:24] Professor:**
> Menos com menos aqui vai dar mais, então em tese é isso aqui. Vai entrar aqui.

**[36:26 - 36:26] Aluna:**
> É.

**[36:27 - 36:28] Professor:**
> É.

**[36:29 - 36:29] Aluna:**
> Agora dá certo.

**[36:30 - 36:30] Professor:**
> Agora dá certo.

**[36:34 - 36:35] Aluna:**
> Mas tem que ter.

**[36:38 - 36:39] Professor:**
> E vai ser o quê?

**[36:40 - 36:40] Aluna:**
> Ele é 120.

**[36:42 - 36:44] Professor:**
> Ele é 120, aqui é 127 menos

**[36:45 - 36:46] Aluna:**
> Isso aí é um quatro, menos.

**[36:46 - 36:46] Professor:**
> Oi?

**[36:47 - 36:48] Aluna:**
> O quarto bit é um.

**[36:50 - 36:51] Professor:**
> Da direita para a esquerda.

**[36:52 - 36:52] Aluna:**
> É.

**[36:57 - 36:58] Aluna:**
> Agora sim, acho que sim.

**[36:59 - 37:04] Professor:**
> E tá certo, né? Isso aqui é 127 menos 4.

**[37:05 - 37:06] Professor:**
> 123.

**[37:09 - 37:10] Aluna:**
> Acho que foi, né?

**[37:13 - 37:15] Professor:**
> Cheio de detalhezinho.

**[37:17 - 37:19] Professor:**
> E aqui, por exemplo, não gerou overflow, né?

**[37:20 - 37:23] Professor:**
> Então não gerou overflow, os números, aliás, melhor dizendo.

**[37:24 - 37:27] Professor:**
> É, aqui não tem flag de overflow, tá tudo certo.

**[37:28 - 37:31] Professor:**
> Essa conta tá certa, sem problema, é ler direto.

**[37:33 - 37:45] Professor:**
> Só não lê direto assim. Em resumo, se você parar para pensar, criar algoritmo, né? Se os números são inteiros com sinal, vai dar tudo certo se não tiver overflow. Eu interpreto direto em todos os casos. Isso é muito legal.

**[37:47 - 37:59] Professor:**
> Quando os números forem, eh, sem sinal, aí é que eu posso ter uma questão de olhar o carry out, né? Pra soma, ou o borrow pra subtração.

**[38:00 - 38:02] Professor:**
> Mas complementador, se não deu overflow, lê direto.

**[38:03 - 38:06] Professor:**
> Isso aqui é positivo, outro é negativo. Acabou. Em resumo é isso.

**[38:07 - 38:11] Aluna:**
> Aí nesse caso, o meu C não estaria tipo como borrow out e ele daria zero, certo?

**[38:12 - 38:13] Professor:**
> Isso.

**[38:14 - 38:29] Professor:**
> Só que ele separou aqui, na hora de exibir, me pede para lembrar todos esses de cabeça, mas na hora de exibir, cada essas flags aqui mostraram, por exemplo, que esse aqui NV, né, seria o no overflow. Tá? Seria, seria isso.

**[38:31 - 38:36] Aluna:**
> E elas só aparecem aí a existência delas indica que elas dão um?

**[38:36 - 38:41] Professor:**
> É. Quando a flag é igual a um, ele escreve. A flag ali é zero.

**[38:42 - 38:48] Aluna:**
> Tá. Então, nesse caso, como ele tá falando ali, não apareceria o NV ou estaria aparecendo o OV?

**[38:50 - 39:01] Professor:**
> Não, aparece os dois. Aqui, ele tá dizendo assim, não houve overflow. Isso é um teste separado. Não houve overflow aqui e, e, e, e, ele tá dizendo aqui que houve borrow.

**[39:02 - 39:03] Aluna:**
> Se tivesse tido overflow,

**[39:03 - 39:05] Professor:**
> em vez do NV teria o A, né?

**[39:06 - 39:11] Professor:**
> Em vez de ele falar, ah, existência dessa flag ou não existência dessa flag, ele só botou uma flag auxiliar

**[39:11 - 39:11] Professor:**
> pra

**[39:12 - 39:14] Professor:**
> poderia ser um nome diferente para um e para zero, exato.

**[39:15 - 39:15] Professor:**
> Tá?

**[39:16 - 39:18] Professor:**
> Só que esse é dele, desse cara aqui.

**[39:18 - 39:19] Professor:**
> Outro seria diferente.

**[39:21 - 39:24] Professor:**
> Então, vamos dizer assim, ah, pra eu saber isso tudo, eu tinha que fazer o quê? Ler um manual.

**[39:25 - 39:31] Professor:**
> Alguns já é maldito, escolher essas letras para ele são intuitivas, né, que eles para você não são, e assim vai.

**[39:31 - 39:32] Professor:**
> Tá.

**[39:33 - 39:35] Professor:**
> Galera, faça esses exercícios aí pra praticar, tá?

**[39:37 - 39:38] Aluna:**
> Todos os exercícios.

**[39:39 - 39:41] Professor:**
> Na aula que vem vamos fazer a nossa querida Alulu, e

**[39:42 - 39:44] Professor:**
> vamos juntar essa bodega toda numa caixa só.

**[39:46 - 39:46] Professor:**
> Bom final de semana.

**[39:47 - 39:47] Aluna:**
> Falou.

**[39:48 - 39:48] Professor:**
> Falou.

**[39:53 - 39:53] Aluna:**
> Professor.

