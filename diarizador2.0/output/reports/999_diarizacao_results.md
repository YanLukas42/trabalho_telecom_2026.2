# Relatório Diarizador 2.0: Separação de Falantes e Otimização MP3

Arquivo de Entrada: `999.mp4` (Tamanho: 22087.24 KB)

| treatment_label                                 |   file_size_kb |   bandwidth_saved_pct |   wer_vs_baseline_320k |   speaker_turns |   total_tokens |   api_latency_sec |
|:------------------------------------------------|---------------:|----------------------:|-----------------------:|----------------:|---------------:|------------------:|
| Baseline 320k Estéreo (Máxima Fidelidade)       |       18171.7  |                 17.73 |                   0    |             128 |          21208 |            41.637 |
| MP3 128k Estéreo (Padrão)                       |        7268.83 |                 67.09 |                  20.43 |             137 |          19865 |            46.472 |
| MP3 64k Mono + Filtro Voz Wideband              |        3634.86 |                 83.54 |                  13.81 |             128 |          23558 |            68.661 |
| MP3 32k Mono + Filtro Voz Wideband              |        1817.6  |                 91.77 |                  18.65 |             135 |          21474 |            30.226 |
| MP3 16k Mono + Filtro Voz Wideband              |         909.02 |                 95.88 |                  20.31 |             118 |          17061 |            12.306 |
| MP3 8k Mono + Filtro Voz Wideband (Ultra-leve)  |         454.73 |                 97.94 |                  43.09 |             159 |          17432 |            13.509 |
| MP3 32k Estéreo (Espacialidade para Diarização) |        1817.51 |                 91.77 |                  16.06 |             118 |          21980 |            31.999 |

## Transcrições Diarizadas por Tratamento

### Baseline 320k Estéreo (Máxima Fidelidade)
- **Tamanho:** `18171.69 KB` (17.73% salvo)
- **Desvio WER vs Baseline 320k:** `0.0%` | **Turnos de Fala:** `128`
- **Transcrição Diarizada:**

```text
[Juiz] Alexander Sousa Silva, essa é uma audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor, se o senhor cometeu o crime ou não, não vai ser verificado agora, tá? O senhor tem direito ao silêncio. O silêncio não será reputado em prejuízo da sua defesa, mas é uma oportunidade do senhor falar sobre a prisão, tá bom? Fazer algumas perguntas pessoais, depois eu vou falar com a da prisão. Nome completo?

[Réu / Bruno] Bruno Alexander Sousa Silva.

[Juiz] Correto? Que cor que o senhor se declara?

[Réu / Bruno] Pardo.

[Juiz] Pardo. O senhor é natural de que cidade?

[Réu / Bruno] São Paulo.

[Juiz] São Paulo. Ah, qual que é o telefone do senhor?

[Réu / Bruno] 11 2747030.

[Juiz] 11 20 747030. O senhor tem algum celular?

[Réu / Bruno] Uhum.

[Réu / Bruno] Não. Não sei de cor, não.

[Juiz] O o e-mail?

[Réu / Bruno] Eh...

[Juiz] Se não souber não tem problema. Não, não se recorda do celular, nem do e-mail.

[Juiz] Ah, o nome da mãe e do pai?

[Réu / Bruno] É, Gizilene Elias de Souza.

[Juiz] Gizilene Elias de Souza. O nome do pai não consta?

[Réu / Bruno] Carlos Roberto Pereira.

[Juiz] Então Gizilene Elias de Souza e Carlos Aberto...

[Réu / Bruno] Roberto.

[Juiz] Carlos Roberto Pereira.

[Réu / Bruno] Silva.

[Juiz] Da Silva. Estado de São Paulo. Estado civil?

[Réu / Bruno] Casado.

[Juiz] Casado. RG?

[Réu / Bruno] 37 101 914-X.

[Juiz] São Paulo, né?

[Réu / Bruno] É.

[Juiz] Ah, o senhor sabe o CPF, senhor?

[Réu / Bruno] Sei.

[Juiz] Qual que é?

[Réu / Bruno] 427 540 498 00.

[Juiz] O senhor mora onde?

[Réu / Bruno] Moro, eh, tem vários endereços, moça.

[Juiz] É, pode falar todos.

[Réu / Bruno] Vou falar só o que eu lembro, que a única rua que eu lembro de cor que foi que eu nasci, Rua Biazi.

[Juiz] Rua Biazi.

[Réu / Bruno] Marcittello.

[Juiz] Marcittello?

[Réu / Bruno] É M A R C H I T T E L L O.

[Juiz] Qual o número?

[Réu / Bruno] 4.

[Juiz] É uma casa?

[Réu / Bruno] Casa.

[Juiz] É quintal não, é só uma casa, mesmo?

[Réu / Bruno] Casa.

[Juiz] Qual que é o bairro?

[Réu / Bruno] São Paulo, Itaquera.

[Juiz] O senhor disse que nasceu nessa casa.

[Réu / Bruno] É.

[Juiz] Mas atualmente o senhor não está lá.

[Réu / Bruno] É, tem a do condomínio que é Condomínio Água.

[Juiz] Mas, eh, onde o senhor dormiu ontem?

[Réu / Bruno] É, Garatá.

[Juiz] E a rua Garatá?

[Réu / Bruno] Não, é, é cidade Garatá.

[Juiz] E qual que é o nome da rua, o senhor sabe?

[Réu / Bruno] Alamidas do Manacás, eu acho.

[Juiz] Alamida...

[Réu / Bruno] Paraíso de Garatá.

[Juiz] O senhor está há quanto tempo nessa rua?

[Réu / Bruno] Dois anos.

[Juiz] O senhor sabe o número?

[Réu / Bruno] Eh...

[Réu / Bruno] 278.

[Juiz] 278. Qual que é o bairro?

[Réu / Bruno] Paraíso de Garatá.

[Juiz] Tem alguma razão para eu especificar aqui que o senhor não saiba direito informar o endereço do senhor? É uma comunidade?

[Réu / Bruno] Não, eu morei tudo já. Endereço.

[Juiz] Tá bom, então qual que não tem certeza?

[Réu / Bruno] Não, é, esse daí, Alamidas do Manacás 278. Paraíso de Garatá.

[Juiz] Tá, o senhor está lá há dois anos.

[Réu / Bruno] Uhum.

[Juiz] É casa alugada?

[Réu / Bruno] Casa própria.

[Juiz] Própria.

[Juiz] O senhor estudou até que grau?

[Réu / Bruno] Superior completo.

[Juiz] Superior?

[Réu / Bruno] É.

[Juiz] Qual que é a faculdade?

[Réu / Bruno] Formado em comércio exterior.

[Juiz] Superior. Tá bom, então tá descendo.

[Juiz] Qual a profissão do senhor?

[Réu / Bruno] Empresário.

[Juiz] Empresário. Quanto que o senhor tem por mês aproximadamente?

[Réu / Bruno] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro.

[Juiz] Mas?

[Réu / Bruno] Média de 1 milhão, 2 milhões.

[Juiz] Por mês?

[Réu / Bruno] Sim.

[Juiz] Tá. Eh, o senhor tem algum dependente?

[Réu / Bruno] Tenho.

[Juiz] Quem?

[Réu / Bruno] A, a minha esposa.

[Juiz] Dependente menor? Ela ou ou...

[Réu / Bruno] Tenho a minha filha, Valentina. E minha mulher tá grávida.

[Juiz] Tá. Quantos meses? Quantos anos tem a, a, a, a Valentina?

[Réu / Bruno] 4 anos.

[Juiz] 4 anos. Qual que é a data de nascimento dela?

[Réu / Bruno] 26 do 6 de 2021.

[Juiz] Ela agora tá com a mãe?

[Réu / Bruno] Uhum.

[Juiz] Tá com a mãe.

[Réu / Bruno] Um outro filho tá na barriga.

[Juiz] Tá bom. A esposa está grávida.

[Réu / Bruno] Seis meses.

[Juiz] Grávida de seis meses. O senhor tem alguma deficiência física, dependência química, doença ou erogênea?

[Réu / Bruno] Não.

[Juiz] Não? Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, de falar com o advogado?

[Réu / Bruno] Sim.

[Juiz] Entendi. O senhor recebeu água potável, alimentação durante a prisão?

[Réu / Bruno] Sim.

[Juiz] Tá. Como é que foi o cumprimento do mandado de prisão?

[Réu / Bruno] Chegaram lá em casa.

[Juiz] Tá.

[Réu / Bruno] Eh, tava dormindo. Só ouvi o barulho da porta batendo. Que a porta é blindada. Eles pedindo pra abrir a porta. Aí eu saí na varanda. Os policial me rendeu na varanda, falou pra eu ficar parado e pediu pra a minha cunhada abrir a porta.

[Juiz] Tá. Eh, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem? Aconteceu alguma coisa?

[Réu / Bruno] Tudo bem.

[Juiz] Tudo bem? O senhor passou por IML?

[Réu / Bruno] Passei.

[Juiz] Tá. O senhor doutor tem alguma pergunta?

[Defensor] Sim, tem, tem perguntas a fazer.

[Juiz] O, o doutor quer constar em ata?

[Defensor] Isso, eh, requerimento, por gentileza.

[Juiz] Ligação para familiar e cobertor.

[Defensor] Isso.

[Juiz] Isso. Tá. Bom, eh, tendo em vista que se trata de carta precatória, não foi verificado nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por esse juízo. Quanto aos requerimentos, novamente, o juízo não eh, não vê problemas na ligação para o familiar e quanto ao cobertor e demais itens pessoais que a defesa queira providenciar, terá que passar pelas deliberações de segurança da custódia. Então, declaro encerrada essa audiência, pode parar a gravação.
```

### MP3 128k Estéreo (Padrão)
- **Tamanho:** `7268.83 KB` (67.09% salvo)
- **Desvio WER vs Baseline 320k:** `20.43%` | **Turnos de Fala:** `137`
- **Transcrição Diarizada:**

```text
[Juíza] Bruna Alexander Souza Silva. Essa é uma audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor, se o senhor cometeu o crime ou não, não vai ser verificado agora, tá? O senhor tem direito ao silêncio, o silêncio não será reputado em prejuízo da sua defesa, mas é uma oportunidade do senhor falar sobre a prisão, tá bom? Fazer algumas perguntas pessoais, depois eu vou falar com a prisão. Nome completo, Bruna Alexander Souza Silva, correto?

[Réu / Bruna Alexander Souza Silva] Correto.

[Juíza] Que cor que o senhor se declara?

[Réu / Bruna Alexander Souza Silva] Pardo.

[Juíza] Pardo. O senhor é natural de que cidade?

[Réu / Bruna Alexander Souza Silva] São Paulo.

[Juíza] São Paulo. Ah. Qual que é o telefone, senhor?

[Réu / Bruna Alexander Souza Silva] Onze, vinte, sete, quatro, setenta, trinta.

[Juíza] Onze, vinte, sete, quatro, setenta, trinta.

[Réu / Bruna Alexander Souza Silva] Uhum.

[Juíza] O senhor tem algum celular?

[Réu / Bruna Alexander Souza Silva] Não, não sei de cor, não.

[Juíza] O, o e-mail?

[Réu / Bruna Alexander Souza Silva] É...

[Juíza] Se não souber, não tem problema. Não, não se recorda do celular nem do e-mail.

[Juíza] Ah, o nome da mãe e do pai?

[Réu / Bruna Alexander Souza Silva] É, Gisleine Elias de Souza.

[Juíza] Gisleine Elias de Souza. O nome do pai não consta.

[Réu / Bruna Alexander Souza Silva] Carlos Roberto Pereira.

[Juíza] Então, Gisleine Elias de Souza e Carlosberto.

[Réu / Bruna Alexander Souza Silva] Roberto.

[Juíza] Carlos Roberto Pereira.

[Réu / Bruna Alexander Souza Silva] Silva.

[Juíza] Da Silva.

[Juíza] Estado de São Paulo. Estado civil?

[Réu / Bruna Alexander Souza Silva] Casado.

[Juíza] Casado. RG?

[Réu / Bruna Alexander Souza Silva] Trinta e sete, cento e um, novecentos e quatorze, traço X.

[Juíza] São Paulo, né?

[Réu / Bruna Alexander Souza Silva] É.

[Juíza] Ah, o senhor sabe o CPF do senhor?

[Réu / Bruna Alexander Souza Silva] Sei.

[Juíza] Qual que é?

[Réu / Bruna Alexander Souza Silva] Quatro, dois, sete, cinco, quatro, zero, quatro, nove, oito, zero, zero.

[Juíza] O senhor mora onde?

[Réu / Bruna Alexander Souza Silva] Moro, é, tem vários endereços, moça.

[Juíza] É? Pode falar todos.

[Réu / Bruna Alexander Souza Silva] Vou, vou falar só o que eu lembro, que a única rua que eu lembro de cor que eu nasci, Rua Biasi.

[Juíza] Rua Biasi.

[Réu / Bruna Alexander Souza Silva] Marchitelo.

[Juíza] Marchitelo?

[Réu / Bruna Alexander Souza Silva] É. M A R C H I T E L L O.

[Juíza] Qual que é o número?

[Réu / Bruna Alexander Souza Silva] Quatro.

[Juíza] É uma casa?

[Réu / Bruna Alexander Souza Silva] Casa.

[Juíza] É quintal, não, é só uma casa mesmo?

[Réu / Bruna Alexander Souza Silva] É casa.

[Juíza] Qual que é o bairro?

[Réu / Bruna Alexander Souza Silva] São Paulo, Itaquera.

[Juíza] Você disse que nasceu nessa casa, mas atualmente o senhor não está lá.

[Réu / Bruna Alexander Souza Silva] É.

[Réu / Bruna Alexander Souza Silva] É. Tem a do condomínio, que é Condomínio Guará.

[Juíza] Mas, é, onde o senhor dormiu ontem?

[Réu / Bruna Alexander Souza Silva] É, Guaratah.

[Juíza] E, a Rua Guaratah?

[Réu / Bruna Alexander Souza Silva] Não, é, é a cidade Guaratah.

[Juíza] E qual o nome da Rua, o senhor não sabe?

[Réu / Bruna Alexander Souza Silva] Alameda do Manacas.

[Juíza] Alameda?

[Réu / Bruna Alexander Souza Silva] Paraíso de Guaratah.

[Juíza] O senhor está há quanto tempo nessa rua?

[Réu / Bruna Alexander Souza Silva] Dois anos.

[Juíza] O senhor sabe o, o número?

[Réu / Bruna Alexander Souza Silva] É, dois, sete, oito.

[Juíza] Dois, sete, oito. Qual que é o bairro?

[Réu / Bruna Alexander Souza Silva] Paraíso de Guaratah.

[Juíza] Tem alguma razão para eu especificar aqui que o senhor não saiba direito informar o endereço do senhor? É, uma comunidade?

[Réu / Bruna Alexander Souza Silva] Não, eu falei tudo já. O endereço.

[Juíza] O que o senhor não tem certeza.

[Réu / Bruna Alexander Souza Silva] Não, é, esse daí Alameda do Manacas, dois, sete, oito.

[Juíza] Dois, sete, oito.

[Réu / Bruna Alexander Souza Silva] Paraíso de Guaratah.

[Juíza] Tá. O senhor está lá há dois anos.

[Réu / Bruna Alexander Souza Silva] Uhum.

[Juíza] É casa alugada?

[Réu / Bruna Alexander Souza Silva] Casa própria.

[Juíza] Própria.

[Juíza] O senhor estudou até que grau?

[Réu / Bruna Alexander Souza Silva] Superior completo.

[Juíza] Superior?

[Réu / Bruna Alexander Souza Silva] Hum.

[Juíza] Qual que é a faculdade?

[Réu / Bruna Alexander Souza Silva] Formado em Comércio Exterior.

[Juíza] Superior.

[Juíza] Então tá bom.

[Juíza] Profissão do senhor?

[Réu / Bruna Alexander Souza Silva] Empresário.

[Juíza] Empresário. Quanto que o senhor tem por mês aproximadamente?

[Réu / Bruna Alexander Souza Silva] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro.

[Juíza] Mas, média de?

[Réu / Bruna Alexander Souza Silva] Um milhão, dois milhão.

[Juíza] Por mês?

[Réu / Bruna Alexander Souza Silva] Sim.

[Juíza] Tá. É, o senhor tem algum dependente?

[Réu / Bruna Alexander Souza Silva] Tenho.

[Juíza] Quem?

[Réu / Bruna Alexander Souza Silva] Ah, minha esposa.

[Juíza] Dependente menor? Ela ou, ou?

[Réu / Bruna Alexander Souza Silva] Tenho. A minha filha, Valentina.

[Juíza] Tá.

[Réu / Bruna Alexander Souza Silva] E minha mulher tá grávida.

[Juíza] Tá. Há seis meses.

[Juíza] Quantos anos tem a, a, a sua, a Valentina?

[Réu / Bruna Alexander Souza Silva] Quatro anos.

[Juíza] Quatro anos. Qual que é a data de nascimento dela?

[Réu / Bruna Alexander Souza Silva] Vinte e seis, do seis, de dois mil e vinte e um.

[Juíza] Ela agora está com a mãe?

[Réu / Bruna Alexander Souza Silva] Uhum.

[Juíza] Está com a mãe.

[Réu / Bruna Alexander Souza Silva] Meu outro filho tá na barriga.

[Juíza] Tá bom.

[Juíza] A esposa está grávida.

[Réu / Bruna Alexander Souza Silva] Seis meses.

[Juíza] Grávida de seis meses.

[Juíza] O senhor tem alguma deficiência física, dependência química, doença ou erogenia?

[Réu / Bruna Alexander Souza Silva] Não.

[Juíza] Não.

[Juíza] Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, de falar com advogado?

[Réu / Bruna Alexander Souza Silva] Sim.

[Juíza] Falar com o advogado? O senhor recebeu água potável, alimentação durante a prisão?

[Réu / Bruna Alexander Souza Silva] Sim.

[Juíza] Tá. Como é que foi o cumprimento do mandado de prisão?

[Réu / Bruna Alexander Souza Silva] Chegaram lá em casa.

[Juíza] Tá.

[Réu / Bruna Alexander Souza Silva] Eh, tava dormindo. Só ouvi o barulho da porta batendo, que a porta é blindada. Eles pedindo para abrir a porta. Aí eu saí na varanda, os policiais me rendeu na varanda, falou para eu ficar parado e pediu para a minha cunhada abrir a porta.

[Juíza] Tá. Eh, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem, aconteceu alguma coisa?

[Réu / Bruna Alexander Souza Silva] Tudo bem.

[Juíza] Tudo bem? O senhor passou pelo IML?

[Réu / Bruna Alexander Souza Silva] Passei.

[Juíza] Tá. Doutor, o senhor quer fazer alguma pergunta?

[Defensora] Tenho perguntas, Doutora.

[Juíza] O, o Doutor está com a sala de inábil?

[Defensora] Sim. Requerimento por gentileza, Doutora. Ligação para familiar e cobertura.

[Réu / Bruna Alexander Souza Silva] Isso.

[Defensora] Isso.

[Juíza] Tá. Bom, tendo em vista que se trata de pauta precatória, não foi verificado nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por esse juízo. Quanto aos requerimentos, obviamente, o juízo, eh, não vê problemas na ligação para o familiar e quanto à cobertura e demais itens pessoais que a defesa queira providenciar, tem que passar antes pelas deliberações de segurança da custódia. Então, declaro encerrada essa audiência. Pode parar a gravação.
```

### MP3 64k Mono + Filtro Voz Wideband
- **Tamanho:** `3634.86 KB` (83.54% salvo)
- **Desvio WER vs Baseline 320k:** `13.81%` | **Turnos de Fala:** `128`
- **Transcrição Diarizada:**

```text
[Juíza] Alexander Souza Silva, essa é uma audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor. Se o senhor cometeu o crime ou não, não vai ser verificado agora, tá? O senhor tem direito ao silêncio, o silêncio não será interpretado em prejuízo da sua defesa, mas é uma oportunidade de o senhor falar sobre a prisão, tá bom? Fazer algumas perguntas pessoais, e depois eu vou falar com a da prisão. Nome completo, Bruno Alexander Souza Silva, correto?
Que cor que o senhor se declara?

[Bruno] Pardo.

[Juíza] O senhor é natural de que cidade?

[Bruno] São Paulo.

[Juíza] São Paulo.
Ah, qual que é o telefone do senhor?

[Bruno] 11 2747030.

[Juíza] 11 20 74 70 30.

[Bruno] Uhum.

[Juíza] O senhor tem algum celular?

[Bruno] Não, não.

[Bruno] Não tenho de cor não.

[Juíza] O e-mail?

[Bruno] É... também não sei.

[Juíza] Se não souber não tem problema. Não, não se recorda do celular nem do e-mail.

[Juíza] Qual o nome da mãe e do pai?

[Bruno] É, Gisleyne Elias de Souza.

[Juíza] Gisleyne Elias de Souza.
O nome do pai não consta?

[Bruno] Carlos Roberto Pereira.

[Juíza] Então, Gisleyne Elias de Souza e Carlos Aberto... Roberto Pereira.

[Bruno] Silva.

[Juíza] Da Silva.
Estado de São Paulo. Estado civil?

[Bruno] Casado.

[Juíza] Casado.
RG?

[Bruno] 37 101 914-X.

[Juíza] São Paulo, né?

[Bruno] É.

[Juíza] Ah, o senhor sabe o CEP do senhor?

[Bruno] Sei.

[Juíza] Qual que é?

[Bruno] 427 540 498 00.

[Juíza] O senhor mora onde?

[Bruno] Moro, eh... tem vários endereços, moça.

[Juíza] É? Pode falar todos.

[Bruno] Eu lembro, vou falar só o que eu lembro, que a única rua que eu lembro de cor que foi que eu nasci, Rua Biazi.

[Juíza] Rua Biazi.

[Bruno] Marchitello.

[Juíza] Marchitello?

[Bruno] É, M A R C H I T T E L L O.

[Juíza] Qual que é o número?

[Bruno] Quatro.

[Juíza] É uma casa?

[Bruno] Casa.

[Juíza] É quintal não, é só uma casa mesmo?

[Bruno] Não.

[Juíza] Qual que é o bairro?

[Bruno] São Paulo, Itaquera.

[Juíza] O senhor disse que nasceu nessa casa.

[Bruno] É.

[Juíza] Mas atualmente o senhor não tá lá.

[Bruno] É, tem o do condomínio que é Condomínio Luan.

[Juíza] Mas, é... onde o senhor dormiu ontem?

[Bruno] É, Garatá.

[Juíza] É, Rua Garatá?

[Bruno] Não, é, é a cidade Garatá.

[Juíza] E qual que é o nome da rua do senhor?

[Bruno] Alameda do Manacás, Caçadores, eu acho. Paraíso de Garatá.

[Juíza] O senhor tá há quantos tempo nessa rua?

[Bruno] Uns dois anos.

[Juíza] O senhor sabe o o número?

[Bruno] É... eu não...

[Bruno] 278.

[Juíza] 278.

[Juíza] Qual que é o bairro?

[Bruno] Paraíso de Garatá.

[Juíza] Tem alguma razão para o senhor especificar aqui que o senhor não saiba direito informar o endereço do senhor? Eh, eu não, não lhe...

[Bruno] Eu não dei tudo já? Endereço?

[Juíza] O que o senhor não tem certeza.

[Bruno] Não, é, é esse daí, Alameda do Manacás, 278. Paraíso de Garatá.

[Juíza] Tá. O senhor tá lá há dois anos.

[Bruno] Uhum.

[Juíza] É casa alugada?

[Bruno] Casa própria.

[Juíza] Própria?

[Juíza] O senhor estudou até que grau?

[Bruno] Superior completo.

[Juíza] Superior?

[Bruno] Hum.

[Juíza] Qual que é a faculdade?

[Bruno] Formado em Comércio Exterior.

[Juíza] Hum.
A profissão do senhor.

[Bruno] Empresário.

[Juíza] Empresário. Quanto que o senhor ganha por mês, aproximadamente?

[Bruno] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro.

[Juíza] Mas, uh, média de 1 milhão, 2 milhão.

[Juíza] Por mês?

[Bruno] Sim.

[Juíza] Tá.
É, o senhor tem algum dependente?

[Bruno] Tenho.

[Juíza] Quem?

[Bruno] A, a minha esposa.

[Juíza] Dependente menor, ela, ou, ou...

[Bruno] Tem. A minha filha, Valentina. E minha mulher tá grávida.

[Juíza] Tá. Então tem dois.

[Juíza] Quantos anos tem a, a, a senhora, a Valentina?

[Bruno] Quatro anos.

[Juíza] Quatro anos. Qual que é a data de nascimento dela?

[Bruno] 26 do 6 de 2021.

[Juíza] Ela agora tá com a mãe?

[Bruno] Uhum.

[Juíza] Tá com.

[Bruno] Meu outro filho tá na barriga.

[Juíza] Tá.
A esposa está grávida.

[Bruno] Seis meses.

[Juíza] Grávida de seis meses.

[Juíza] O senhor tem alguma deficiência física, dependência química, doença ou hermogênia?

[Bruno] Não.

[Juíza] Não.

[Juíza] Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, de falar com o advogado?

[Bruno] Sim.

[Juíza] Falar.

[Juíza] O senhor recebeu água potável, alimentação durante a prisão?

[Bruno] Sim.

[Juíza] Tá. Como é que foi o cumprimento do mandado de prisão?

[Bruno] Chegaram lá em casa.

[Juíza] Tá.

[Bruno] Eh... tava dormindo. Só ouvi o barulho da porta batendo, que a porta é blindada, eles pedindo para abrir a porta. Aí eu saí na varanda, um policial me rendeu na varanda, falou pra eu ficar parado, e pediu pra a minha cunhada abrir a porta.

[Juíza] Tá.
É, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem? Aconteceu alguma coisa?

[Bruno] Tudo bem.

[Juíza] Tudo bem? O senhor passou por IML?

[Bruno] Passei.

[Juíza] Tá. O senhor tem alguma coisa, alguma pergunta?

[Bruno] Umas perguntas, moça.

[Juíza] O, o doutor tem alguma?

[Advogado] Temos, é, requerimento, por gentileza.

[Juíza] Ligação para familiar.

[Advogado] E cobertor.

[Juíza] Isso.

[Juíza] Tá.
Bom, eh, tendo em vista que se trata de cadeia precatória, não foi verificado nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por esse juízo. Eh, quanto aos requerimentos, novamente, o juízo, eh, não vê problemas na ligação para o familiar e quanto ao cobertor e demais itens pessoais que a defesa queira providenciar, tem que passar antes pelas deliberações de segurança da custódia.
Então, declarada encerrada essa audiência, pode parar a gravação.
```

### MP3 32k Mono + Filtro Voz Wideband
- **Tamanho:** `1817.6 KB` (91.77% salvo)
- **Desvio WER vs Baseline 320k:** `18.65%` | **Turnos de Fala:** `135`
- **Transcrição Diarizada:**

```text
[Juíza] Bruna Alexander Souza Silva. Essa é uma audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor, se o senhor cometeu crime ou não, não vai ser verificado agora, tá? O senhor tem direito a silêncio, o seu silêncio não será interpretado em prejuízo da sua defesa, mas é uma oportunidade de o senhor falar sobre a prisão, tá bom? Vou fazer algumas perguntas pessoais e depois eu vou para a questão da prisão. Nome completo, Bruno Alexander Souza Silva, correto?

[Réu / Bruno] Correto.

[Juíza] Que cor que o senhor se declara?

[Réu / Bruno] Pardo.

[Juíza] Pardo. O senhor é natural de que cidade?

[Réu / Bruno] São Paulo.

[Juíza] São Paulo.

[Juíza] Ah, qual que é o telefone do senhor?

[Réu / Bruno] 11 2747030.

[Juíza] 11 27 74 70 30.

[Réu / Bruno] Uhum.

[Juíza] O senhor tem algum celular?

[Réu / Bruno] Não, não sei de cor, não.

[Juíza] O e-mail?

[Réu / Bruno] É...

[Juíza] Se não souber, não tem problema. Não, não se recorda do celular nem do e-mail.

[Juíza] O nome da mãe e do pai?

[Réu / Bruno] É, Gisleine Elias de Souza.

[Juíza] Gisleine Elias de Souza. O nome do pai não consta?

[Réu / Bruno] Carlos Roberto Pereira.

[Juíza] Então Gisleine Elias de Souza e Carlos Roberto?

[Réu / Bruno] Roberto.

[Juíza] Carlos Roberto Pereira.

[Réu / Bruno] Silva.

[Juíza] Da Silva.

[Juíza] Estado de São Paulo, né? Estado civil?

[Réu / Bruno] Casado.

[Juíza] Casado.

[Juíza] RG?

[Réu / Bruno] 37 101 914 traço x.

[Juíza] São Paulo, né?

[Réu / Bruno] É.

[Juíza] O senhor sabe o CPF do senhor?

[Réu / Bruno] Sei.

[Juíza] Qual que é?

[Réu / Bruno] 427 540 498 00.

[Juíza] O senhor mora onde?

[Réu / Bruno] Moro, é, tem vários endereços, mans.

[Juíza] É, pode falar todos.

[Réu / Bruno] Vou, só vou falar o que eu lembro, porque a única rua que eu lembro de cor que eu nasci, Rua Biazi...

[Juíza] Rua Biazi.

[Réu / Bruno] Marchitello.

[Juíza] Marchitello? É M A...

[Réu / Bruno] É, M A R C H I T T E L L O.

[Juíza] Qual o número?

[Réu / Bruno] Quatro.

[Juíza] É uma casa?

[Réu / Bruno] Casa.

[Juíza] É quintal, não? É só uma casa mesmo.

[Réu / Bruno] Isso.

[Juíza] Qual que é o bairro?

[Réu / Bruno] São Paulo, Itaquera.

[Juíza] O senhor disse que nasceu nessa casa, né? Mas atualmente o senhor não tá lá?

[Réu / Bruno] É, tem o condomínio que é, Condomínio Aruanã.

[Juíza] Mas, é, onde o senhor dormiu ontem?

[Réu / Bruno] É Garatá.

[Juíza] E, a Rua Garatá?

[Réu / Bruno] Não, é, é a cidade Garatá.

[Juíza] E qual que é o nome da rua, o senhor sabe?

[Réu / Bruno] Alamendas do Manacá, foi onde...

[Juíza] Alamendas...

[Réu / Bruno] Paraíso de Garatá.

[Juíza] O senhor tá há quanto tempo nessa rua?

[Réu / Bruno] Uns dois anos.

[Juíza] O senhor sabe o número?

[Réu / Bruno] É...

[Réu / Bruno] 278.

[Juíza] 278.

[Juíza] Qual que é o bairro?

[Réu / Bruno] Paraíso de Garatá.

[Juíza] Tem alguma razão que o senhor especificar aqui que o senhor não saiba direito informar o endereço do senhor? A comunidade...

[Réu / Bruno] Mudei tudo já, endereço.

[Juíza] Você falou que não tem certeza.

[Réu / Bruno] Não, é, esse daí Alameda do Manacás 278.

[Juíza] 278.

[Réu / Bruno] Paraíso de Garatá.

[Juíza] Tá. O senhor tá lá há dois anos.

[Réu / Bruno] Uhum.

[Juíza] É casa alugada?

[Réu / Bruno] Casa própria.

[Juíza] Própria.

[Juíza] O senhor estudou até que grau?

[Réu / Bruno] Superior completo.

[Juíza] Superior?

[Réu / Bruno] Hum.

[Juíza] Qual que é a faculdade?

[Réu / Bruno] Formado em comércio exterior.

[Juíza] A profissão do senhor?

[Réu / Bruno] Empresário.

[Juíza] Empresário. Quanto que o senhor ganha por mês aproximadamente?

[Réu / Bruno] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro.

[Juíza] Mas em média?

[Réu / Bruno] Em média de um milhão, dois milhão.

[Juíza] Por mês?

[Réu / Bruno] Sim.

[Juíza] É, o senhor tem algum dependente?

[Réu / Bruno] Tenho.

[Juíza] Quem?

[Réu / Bruno] A minha esposa.

[Juíza] Dependente menor? Ela ou ou...

[Réu / Bruno] Tem, a minha filha, Valentina. E minha mulher tá grávida.

[Juíza] Tá. Quantos anos tem a, a, a Valentina?

[Réu / Bruno] Quatro anos.

[Juíza] Quatro anos. Qual que é a data de nascimento dela?

[Réu / Bruno] 26 do 6 de 2021.

[Juíza] Ela agora tá com a mãe?

[Réu / Bruno] Uhum.

[Juíza] Tá com a mãe.

[Réu / Bruno] O outro filho tá na barriga.

[Juíza] A esposa está grávida.

[Réu / Bruno] Seis meses.

[Juíza] Grávida de seis meses.

[Juíza] O senhor tem alguma deficiência física, dependência química, doença ou é homogêneo?

[Réu / Bruno] Não.

[Juíza] Não? Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, de falar com advogado?

[Réu / Bruno] Sim.

[Juíza] De falar. O senhor recebeu água potável, alimentação, durante a prisão?

[Réu / Bruno] Sim.

[Juíza] Tá. Como é que foi o cumprimento do mandado de prisão?

[Réu / Bruno] Chegaram lá em casa.

[Juíza] Tá.

[Réu / Bruno] É, estava dormindo. Só ouvi o barulho da porta batendo, que a porta é blindada, eles pedindo pra abrir a porta. Aí eu saí na varanda, uns policial me rendeu na varanda, mandou pra eu ficar parado e pediu pra a minha cunhada abrir a porta.

[Juíza] Tá. É, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem? Alguma coisa?

[Réu / Bruno] Tudo bem.

[Juíza] Tudo bem? O senhor passou pro IML?

[Réu / Bruno] Passei.

[Juíza] Tá. O senhor tem algum pedido pra fazer, o senhor ou, né, sua defesa, tem alguma pergunta pra fazer?

[Réu / Bruno] Não, sem perguntas.

[Defensora] Eu tenho, doutora.

[Juíza] Ah, tá. Qual, doutora?

[Defensora] Mesmos, é, requerimento com urgência de ligação para familiar e cobertor.

[Juíza] Ligação para familiar e cobertor.

[Defensora] Isso.

[Juíza] Isso.

[Juíza] Bom, ah, tendo em vista que se trata de caráter precatória, não foi verificado nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por este juízo. Quanto aos requerimentos, obviamente o juízo não, eh, não vê problemas na ligação para um familiar e quanto ao cobertor e demais itens pessoais que a defesa requereu providenciar, tem que passar pelas deliberações de segurança da custódia. Então, declararei encerrada essa audiência, pode parar a gravação.
```

### MP3 16k Mono + Filtro Voz Wideband
- **Tamanho:** `909.02 KB` (95.88% salvo)
- **Desvio WER vs Baseline 320k:** `20.31%` | **Turnos de Fala:** `118`
- **Transcrição Diarizada:**

```text
[Juiz] Bruno Alexander Souza Silva, é sua audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor, se o senhor cometeu o crime ou não, não vai ser verificado agora, tá? O senhor tem direito ao silêncio, o silêncio não será reputado em prejuízo da sua defesa, mas é uma oportunidade para o senhor falar sobre a prisão, tá bom? Faço algumas perguntas pessoais, depois eu vou para a condenação. Nome completo: Bruno Alexander Souza Silva, correto? Ah, e qual que o senhor se declara?
[Réu / Bruno] Pardo.
[Juiz] Pardo. O senhor é natural de cidade?
[Réu / Bruno] São Paulo.
[Juiz] São Paulo. Ah, qual que é o telefone, senhor?
[Réu / Bruno] 11 2747030.
[Juiz] 11 20 747030?
[Réu / Bruno] Uhum.
[Juiz] O senhor tem algum celular?
[Réu / Bruno] Não, não sei de cor não.
[Juiz] O e-mail?
[Réu / Bruno] É,
[Juiz] Se o senhor não souber, não tem problema. Não, não se recorda de celular nem e-mail. Ah, o nome da mãe e do pai?
[Réu / Bruno] É, Gisleny Elias de Souza.
[Juiz] Gisleny Elias de Souza. O nome do pai não consta.
[Réu / Bruno] Carlos Roberto Pereira.
[Juiz] Então, Gisleny Elias de Souza e Carlos Roberto.
[Réu / Bruno] Roberto.
[Juiz] Carlos Roberto Pereira.
[Réu / Bruno] Silva.
[Juiz] Da Silva. São Paulo, estado civil?
[Réu / Bruno] Casado.
[Juiz] Casado. RG?
[Réu / Bruno] 37 101 914-X.
[Juiz] São Paulo, né?
[Réu / Bruno] É. Ah, o senhor sabe o seu CPF, senhor?
[Réu / Bruno] Sei.
[Juiz] Qual que é?
[Réu / Bruno] 427 540 498 00.
[Juiz] O senhor mora onde?
[Réu / Bruno] Moro, eh, tem vários endereços, moça.
[Juiz] É, pode falar todos.
[Réu / Bruno] Vou falar só o que eu lembro, que é a única rua que eu lembro de cor, que eu pertencia. Rua Biazi,
[Juiz] Rua Biazi.
[Réu / Bruno] Marchitello.
[Juiz] Marchitello?
[Réu / Bruno] É, M A
[Juiz] R C H I T E L L O.
[Réu / Bruno] Aí, T T
[Juiz] E L L O. Qual o número?
[Réu / Bruno] 4.
[Juiz] É uma casa?
[Réu / Bruno] Casa.
[Juiz] É um quintal, não? É só uma casa mesmo. Qual que é o bairro?
[Réu / Bruno] São Paulo, Itaquera. O senhor disse que nasceu nessa casa.
[Réu / Bruno] É.
[Juiz] Mas atualmente o senhor não está lá.
[Réu / Bruno] Não. É, tem lá do condomínio, que é condomínio Iguana.
[Juiz] Mas, é, onde o senhor dormiu ontem?
[Réu / Bruno] É, em Guaratinguetá.
[Juiz] Guaratinguetá?
[Réu / Bruno] Não, é, é a cidade de Guaratinguetá.
[Juiz] E qual que é o nome da rua, se o senhor souber?
[Réu / Bruno] Alamedas do Manacás, Vionche.
[Juiz] Alamedas.
[Réu / Bruno] Paraíso de Guaratinguetá.
[Juiz] O senhor está há quanto tempo nessa rua?
[Réu / Bruno] Dois anos.
[Juiz] O senhor sabe o número?
[Réu / Bruno] É, 278.
[Juiz] 278. Qual que é o bairro?
[Réu / Bruno] Paraíso de Guaratinguetá. Tem alguma razão para que o senhor não saiba direito informar o endereço do senhor? Eh, tem alguma dificuldade. O senhor mora em um apartamento?
[Réu / Bruno] Eu moro em tudo já. Endereço.
[Juiz] Qual que o senhor tem certeza?
[Réu / Bruno] Não, é, esse daí é Alamedas do Manacás, 278.
[Juiz] 278.
[Réu / Bruno] Paraíso de Guaratinguetá.
[Juiz] Tá. O senhor está lá há dois anos.
[Réu / Bruno] Uhum.
[Juiz] É casa alugada?
[Réu / Bruno] Casa própria.
[Juiz] Própria. O senhor estuda até que grau?
[Réu / Bruno] Superior completo.
[Juiz] Superior?
[Réu / Bruno] Uhum.
[Juiz] Qual que é a faculdade?
[Réu / Bruno] Formado em Comércio Exterior. Ocupação, senhor?
[Réu / Bruno] Empresário.
[Juiz] Empresário. Quanto que o senhor tem de remuneração?
[Réu / Bruno] Varia, depende da publicidade. Tem mês que tem um valor, tem mês que é outro.
[Juiz] Mas uma média tem 1 milhão, 2 milhão?
[Réu / Bruno] Por mês? Sim.
[Juiz] Tá. Eh, o senhor tem algum dependente?
[Réu / Bruno] Tenho.
[Juiz] Quem?
[Réu / Bruno] A, a, minha esposa. Dependente menor? Ela ou ou?
[Réu / Bruno] Tenho. A, a minha filha, Valentina.
[Juiz] E minha mulher está grávida.
[Réu / Bruno] Tá.
[Juiz] Quantos anos tem a, a, a senhor, a?
[Réu / Bruno] Quatro anos.
[Juiz] Quatro anos. Qual que é a data de nascimento dela?
[Réu / Bruno] 26 do 6 de 2021.
[Juiz] Ela mora com a mãe?
[Réu / Bruno] Uhum.
[Juiz] Tá com a mãe.
[Réu / Bruno] Meu outro filho tá na barriga.
[Juiz] É. Minha esposa está grávida. Seis meses.
[Réu / Bruno] Grávida de seis meses.
[Juiz] O senhor tem alguma deficiência física, deficiência química, doença ou algo do gênero?
[Réu / Bruno] Não. Não?
[Juiz] Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, de falar com advogado?
[Réu / Bruno] Sim.
[Juiz] Tá. O senhor recebeu água potável, alimentação durante a prisão?
[Réu / Bruno] Sim.
[Juiz] Tá. Como é que foi o cumprimento do mandado de prisão?
[Réu / Bruno] Chegaram lá em casa.
[Juiz] Tá.
[Réu / Bruno] Eh, tava dormindo. Só ouvi o barulho da porta batendo, que a porta é blindada. Eles pediram para abrir a porta. Aí eu saí na varanda, os policiais me renderam na varanda, falou para eu ficar parado, e pediu para a, a minha cunhada abrir a porta.
[Juiz] Tá. Eh, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem? Aconteceu alguma coisa?
[Réu / Bruno] Tudo bem.
[Juiz] Tudo bem? O senhor passou por IML?
[Réu / Bruno] Passei.
[Juiz] Tá. Vamos para as perguntas.
[Defensora] O, o, o Dr. Capeta constava.
[Juiz] Ligações para familiar.
[Defensora] Isso. E cobertor.
[Juiz] Isso. Tá. Bom, eh, tendo em vista que se trata de caráter precatório, não foi verificada nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por esse juiz. Eh, quanto aos requerimentos, novamente, o juízo não eh, não vê problemas na ligação para o familiar e quanto ao cobertor e demais itens pessoais que ainda precisarão providenciar, tem que passar antes pelas deliberações de segurança da custódia. Então, declarada encerrada essa audiência, pode parar a gravação.
```

### MP3 8k Mono + Filtro Voz Wideband (Ultra-leve)
- **Tamanho:** `454.73 KB` (97.94% salvo)
- **Desvio WER vs Baseline 320k:** `43.09%` | **Turnos de Fala:** `159`
- **Transcrição Diarizada:**

```text
[Juíza] Bruno Alexandre Souza Silva, a audiência de custódia, a audiência de custódia, que tem por objetivo apenas verificar a prisão do senhor, se está com alguma tortura, não, não vai ser verificado agora, tá? Eu sei que o senhor tem deficiência, o senhor não será escutado em relação aos fatos da queixa, mas é uma oportunidade para o senhor falar sobre a prisão, tá bom? Vou fazer algumas perguntas pessoais e depois eu vou perguntar para o senhor da prisão. O nome completo?
[Réu / Bruno] Bruno Alexandre Souza Silva.
[Juíza] Correto? O que é o que o senhor declara?
[Réu / Bruno] Eu sou pardo.
[Juíza] Pardo. Senhor, é natural de que cidade?
[Réu / Bruno] São Paulo.
[Juíza] São Paulo. Ah, qual que é o seu telefone, senhor?
[Réu / Bruno] 11947030.
[Juíza] 11947030. Uhum. O celular?
[Réu / Bruno] Não, não sei qual, não.
[Juíza] Não. O e-mail?
[Réu / Bruno] É. Não se declara, não tem problema. Não, não se recorda do celular nem do e-mail.
[Réu / Bruno] Não.
[Juíza] Tá. Qual o nome da mãe e do pai?
[Réu / Bruno] É, Isleni e Dijo Souza.
[Juíza] Isleni e Dijo Souza. O nome do pai não consta.
[Réu / Bruno] Carlos Alberto Pereira.
[Juíza] Então, Isleni e Dijo Souza e Carlos Alberto.
[Réu / Bruno] Roberto.
[Juíza] Carlos Roberto Pereira.
[Réu / Bruno] Sim.
[Juíza] Da Silva.
[Réu / Bruno] Da Silva.
[Juíza] Estado: São Paulo, Estado Civil?
[Réu / Bruno] Casado.
[Juíza] Casado. RG?
[Réu / Bruno] 36.
[Juíza] 36?
[Réu / Bruno] 101.
[Juíza] 964243.
[Réu / Bruno] 964243030.
[Juíza] São Paulo, né?
[Réu / Bruno] É.
[Juíza] CPF.
[Réu / Bruno] Sim.
[Juíza] Ok. Qual que é o seu CEP?
[Réu / Bruno] 540.
[Juíza] 540.
[Réu / Bruno] 498.
[Juíza] 498.
[Réu / Bruno] 00.
[Juíza] 00. O senhor mora onde?
[Réu / Bruno] Moro, eh, rua. Vou dar o endereço, né?
[Juíza] Pode, pode falar tudo.
[Réu / Bruno] Alameda do Manezinhos, é a única rua no meu condomínio que é, condomínio de Cordeiro, de quem eu nasci. Alameda.
[Juíza] Alameda.
[Réu / Bruno] Marchitelo.
[Juíza] Marchitelo.
[Réu / Bruno] É, M.A.
[Réu / Bruno] R.C.H.
[Réu / Bruno] I.
[Réu / Bruno] E T.E.
[Réu / Bruno] L.L.O.
[Juíza] Ok. Número?
[Réu / Bruno] Quatro.
[Juíza] É uma casa?
[Réu / Bruno] Casa.
[Juíza] É quintal, não. É só uma casa mesmo. Qual que é o bairro?
[Réu / Bruno] São Paulo, Itaqui.
[Juíza] O senhor disse que nasceu nessa casa.
[Réu / Bruno] É.
[Juíza] Mas atualmente o senhor não mora.
[Réu / Bruno] É, tem um condomínio que é, condomínio é agora.
[Juíza] Mas, eh, onde o senhor dormiu ontem?
[Réu / Bruno] Eh, em Garatá.
[Juíza] E que rua de Garatá?
[Réu / Bruno] Não, é, é a cidade de Garatá.
[Juíza] E qual que é o nome da rua do senhor?
[Réu / Bruno] Alameda do Maneca, 278.
[Juíza] Maneca.
[Réu / Bruno] Rais de Garatá.
[Juíza] Ah, o senhor está há quanto tempo nessa rua?
[Réu / Bruno] Dois anos.
[Juíza] Dois anos.
[Juíza] O senhor está no número?
[Réu / Bruno] É.
[Réu / Bruno] Onde está o número?
[Réu / Bruno] 278.
[Juíza] 278.
[Juíza] Qual que é o bairro?
[Réu / Bruno] Rais de Garatá.
[Juíza] Tem alguma razão para que o senhor não saiba direito o informal, o endereço? Ah, moro em tudo, já?
[Réu / Bruno] É.
[Réu / Bruno] Endereço.
[Juíza] O senhor, o senhor tem certeza?
[Réu / Bruno] Não, é, este é Alameda do Maneca, 278.
[Juíza] 278.
[Réu / Bruno] Rais de Garatá.
[Juíza] Tá. O senhor está lá há dois anos.
[Réu / Bruno] Uhum.
[Juíza] É casa alugada?
[Réu / Bruno] Casa própria.
[Juíza] Própria?
[Juíza] O senhor está aqui, graduando?
[Réu / Bruno] Superior completo.
[Juíza] Superior?
[Réu / Bruno] Hum.
[Juíza] Qual que é a sua formação?
[Réu / Bruno] Formado em Comércio Exterior.
[Juíza] Certo.
[Juíza] O senhor tem empregado?
[Réu / Bruno] Trabalhador.
[Juíza] Empregado. O que que o senhor ganha por mês aproximadamente?
[Réu / Bruno] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro.
[Juíza] Mas, hum.
[Réu / Bruno] Na média, 1.000, 2.000.
[Juíza] Por mês?
[Réu / Bruno] Sim.
[Juíza] Tá. O senhor tem dependentes?
[Réu / Bruno] Tenho.
[Juíza] Quem?
[Réu / Bruno] Ah, a esposa.
[Juíza] Você que é menor, tá lá. É.
[Réu / Bruno] Tem. Ah, minha filha, Valentina.
[Juíza] Hã.
[Réu / Bruno] E minha mulher tá grávida.
[Juíza] Tá. No seu.
[Réu / Bruno] Os dois.
[Juíza] Quantos anos tem a, a, a sua, a sua Valentina?
[Réu / Bruno] Quatro anos.
[Juíza] Quatro anos. Qual que é a data de nascimento dela?
[Réu / Bruno] 26.
[Réu / Bruno] Do seis de 2021.
[Juíza] O senhor mora com quem?
[Réu / Bruno] Uhum.
[Réu / Bruno] Tá com ele.
[Juíza] O senhor mora com quem?
[Réu / Bruno] Uma outra filha, tá na barriga.
[Juíza] Tá na barriga.
[Juíza] Uma esposa e está grávida.
[Réu / Bruno] Seis meses.
[Juíza] Está grávida, seis meses.
[Juíza] O senhor tem alguma deficiência física, deficiência psíquica, doença ou é homogêneo?
[Réu / Bruno] Não.
[Juíza] Não.
[Juíza] Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais? Falar, pode [ininteligível].
[Réu / Bruno] Sim.
[Juíza] Sim. Foi, recebeu água potável, alimentação, depois da prisão?
[Réu / Bruno] Sim.
[Juíza] Tá. Como é que foi o cumprimento do mandado de prisão?
[Réu / Bruno] Chegaram lá em casa. Tá.
[Réu / Bruno] Eh.
[Réu / Bruno] Estava dormindo.
[Réu / Bruno] Ah.
[Réu / Bruno] Só do barulho da porta batendo, que a porta é blindada. Eles pediram para abrir a porta. Aí eu saí na varanda. O policial me viu na varanda, falou para eu ficar parado, e pediu para, a minha cunhada abrir a porta.
[Juíza] Eh, o senhor está com alguma lesão ou está tudo bem? O senhor está falando com a coisa?
[Réu / Bruno] Tudo bem.
[Juíza] Tudo bem? O senhor passou por exame?
[Réu / Bruno] Passei.
[Juíza] Tá. O senhor está contando tudo?
[Réu / Bruno] Não, sim, tudo bem.
[Juíza] O doutor te contou?
[Réu / Bruno] Me contou.
[Juíza] O doutor te contou também, né?
[Réu / Bruno] E ligação para familiar, e conversar.
[Juíza] O doutor.
[Réu / Bruno] Isso.
[Juíza] Tá. Bom, eh, tendo em vista que, de fato, a declaratória, não foi verificada nenhuma mácula no cumprimento do mandado de prisão, não há nenhuma providência a ser tomada por este juízo. Eh, enquanto ao círculo do mês, novamente, o juiz não, eh, não vê problemas na ligação para o familiar, enquanto ao defensor de mais deferências para se fazer à defesa, para se liberarem seguranças da custódia. Em relação ao artigo 310, parágrafo 3º.
```

### MP3 32k Estéreo (Espacialidade para Diarização)
- **Tamanho:** `1817.51 KB` (91.77% salvo)
- **Desvio WER vs Baseline 320k:** `16.06%` | **Turnos de Fala:** `118`
- **Transcrição Diarizada:**

```text
[Juíza] Alexander Souza Silva. Essa é uma audiência de custódia. A audiência de custódia tem por objetivo apenas verificar a prisão do senhor, se o senhor cometeu o crime ou não, não vai ser verificado agora, tá? O senhor tem direito ao silêncio, o silêncio não será interpretado em prejuízo da sua defesa, mas é uma oportunidade do senhor falar sobre a prisão, tá bom? Fazer algumas perguntas pessoais, depois eu vou pra [inaudível] da prisão. Nome completo: Bruna Alexander Souza Silva, correto? Que cor que o senhor se declara?

[Réu / Bruno] Pardo.

[Juíza] Pardo. O senhor é natural de que cidade?

[Réu / Bruno] São Paulo.

[Juíza] São Paulo. Qual que é o telefone do senhor?

[Réu / Bruno] 11 27 470 30.

[Juíza] 11 20 74 70 30.

[Réu / Bruno] Uhum.

[Juíza] O senhor tem algum celular?

[Réu / Bruno] Não. Não sei de cor, não.

[Juíza] O, o e-mail?

[Réu / Bruno] É...

[Juíza] Tudo bem, se não souber não tem problema. Não, não se recorda do celular nem do e-mail. Nome da mãe e do pai?

[Réu / Bruno] É, Gislene Elias de Souza.

[Juíza] Gislene Elias de Souza. O nome do pai não consta?

[Réu / Bruno] Carlos Roberto Pereira.

[Juíza] Então Gislene Elias de Souza e Carlos Aberto Roberto. Carlos Roberto Pereira.

[Réu / Bruno] Da Silva.

[Juíza] Da Silva. Estado de São Paulo, estado civil?

[Réu / Bruno] Casado.

[Juíza] Casado. RG?

[Réu / Bruno] 37 101 914 traço X.

[Juíza] São Paulo, né?

[Réu / Bruno] É.

[Juíza] O senhor sabe o seu CPF, senhor?

[Réu / Bruno] Sei.

[Juíza] Qual que é? 427 540 498 00. O senhor mora onde?

[Réu / Bruno] Moro, eh, tenho vários endereços, moça.

[Juíza] É, pode falar todos.

[Réu / Bruno] Vou, vou falar só o que eu lembro, porque a única rua que eu lembro de cor que eu nasci, Rua Biazi.

[Juíza] Rua Biazi.

[Réu / Bruno] Marchitello.

[Juíza] Marchitello.

[Réu / Bruno] É M A R C H I T T E L L O.

[Juíza] Qual que é o número?

[Réu / Bruno] 4.

[Juíza] É uma casa?

[Réu / Bruno] Casa.

[Juíza] É, quintal, não. É só uma casa mesmo?

[Réu / Bruno] Casa.

[Juíza] Qual que é o bairro? São Paulo Itaquera.

[Réu / Bruno] Itaquera.

[Juíza] O senhor disse que nasceu nessa casa.

[Réu / Bruno] É.

[Juíza] Mas atualmente o senhor não tá lá.

[Réu / Bruno] É, tem a do condomínio, que é Condomínio Água.

[Juíza] Mas, eh, onde o senhor dormiu ontem?

[Réu / Bruno] É, Guaratinguetá.

[Juíza] Em, a Rua Guaratinguetá?

[Réu / Bruno] Não, é, é a cidade, Guaratinguetá.

[Juíza] E qual o nome da rua, o senhor sabe?

[Réu / Bruno] Alamandas do Manacá, Caehon. Alamandas Paraíso de Guaratinguetá.

[Juíza] O senhor está há quanto tempo nessa rua?

[Réu / Bruno] Dois anos.

[Juíza] O senhor sabe o, o número?

[Réu / Bruno] É... 278.

[Juíza] 278. Qual que é o bairro?

[Réu / Bruno] Paraíso de Guaratinguetá.

[Juíza] Tem alguma razão, pelo que eu especifiquei aqui, que o senhor não saiba direito informar o endereço do senhor? Eh, como disse, morou em tudo já?

[Réu / Bruno] Endereço?

[Juíza] O senhor falou que não tem certeza.

[Réu / Bruno] Não, é, essa daí, Alamandas do Manacás 278, Paraíso de Guaratinguetá.

[Juíza] Tá, o senhor está lá há dois anos.

[Réu / Bruno] Uhum.

[Juíza] É, casa alugada?

[Réu / Bruno] Casa própria.

[Juíza] Própria? O senhor estudou até que grau?

[Réu / Bruno] Superior completo.

[Juíza] Superior?

[Réu / Bruno] Hum.

[Juíza] Qual que é a faculdade?

[Réu / Bruno] Formado em Comércio Exterior.

[Juíza] Superior. Eh, profissão do senhor?

[Réu / Bruno] Empresário.

[Juíza] Empresário. Quanto que o senhor tem de renda, aproximadamente?

[Réu / Bruno] Varia, depende da publicidade. Tem mês que é um valor, tem mês que é outro. Em média, de 1 milhão, 2 milhão.

[Juíza] Por mês?

[Réu / Bruno] Sim.

[Juíza] Eh, o senhor tem algum dependente?

[Réu / Bruno] Tenho.

[Juíza] Quem?

[Réu / Bruno] Ah, minha esposa.

[Juíza] Dependente menor, ela tem ou ou?

[Réu / Bruno] Tem, ah, minha filha, Valentina, e minha mulher tá grávida.

[Juíza] Tá, então

[Réu / Bruno] dois.

[Juíza] Quantos anos tem a, a sua, a Valentina?

[Réu / Bruno] Quatro anos.

[Juíza] Quatro anos. Qual que é a data de nascimento dela?

[Réu / Bruno] 26 do 6 de 2021.

[Juíza] Ela agora está com a mãe?

[Réu / Bruno] Uhum.

[Juíza] Está com a mãe.

[Réu / Bruno] Meu outro filho tá na barriga.

[Juíza] A esposa está grávida.

[Réu / Bruno] Seis meses.

[Juíza] Grávida de seis meses. O senhor tem alguma deficiência física, deficiência química, doença ou é homogêneo?

[Réu / Bruno] Não.

[Juíza] Não. Tá. Quando o senhor foi preso, foi dada a ciência dos direitos constitucionais, falar com o advogado?

[Réu / Bruno] Sim.

[Juíza] Sim. O senhor recebeu água potável, alimentação desde a prisão?

[Réu / Bruno] Sim.

[Juíza] Tá. Como é que foi o cumprimento do mandado de prisão?

[Réu / Bruno] Chegaram lá em casa.

[Juíza] Tá.

[Réu / Bruno] Eh, tava dormindo. Só ouvi o barulho da porta batendo, que a porta é blindada, eles pedindo pra abrir a porta. Aí eu saí na varanda, os policiais me renderam na varanda, falou pra eu ficar parado e pediu pra a minha cunhada abrir a porta.

[Juíza] Tá. Eh, o senhor tem alguma coisa a relatar sobre o cumprimento da prisão? Foi tudo bem? Aconteceu alguma coisa?

[Réu / Bruno] Tudo bem.

[Juíza] Tudo bem? O senhor passou pro IML?

[Réu / Bruno] Passei.

[Juíza] Tá. O senhor tem alguma coisa a perguntar, alguma dúvida?

[Defensora] Não, sem perguntas.

[Juíza] Não, tem perguntas do doutor. O, o doutor quer fazer um requerimento em algo?

[Defensora] Não, ele tem um requerimento, por gentileza.

[Juíza] Ligação para familiar e cobertor.

[Defensora] Isso.

[Juíza] Isso. Tá. Bom, ah, tendo em vista que se trata de carta precatória, não foi verificado nenhuma mácula no cumprimento do mandado de prisão e não há nenhuma providência a ser tomada por esse juízo. Ah, quanto aos requerimentos, novamente, o juiz, eh, não vê problemas na ligação para um familiar e quanto ao cobertor e demais itens pessoais que a defesa queira providenciar, em que passar das deliberações de segurança da custódia. Então, declaro encerrada essa audiência. Pode parar a gravação.
```

