# Histórias de usuário da Pauta

A Pauta transforma a gravação de uma aula de inglês em atividades individuais para cada aluno e em um plano para a
próxima aula. Este documento descreve o que o professor precisa fazer, na linguagem dele. As regras que sustentam cada
história estão em [regras-de-negocio.md](regras-de-negocio.md) (códigos `RN-xx`).

**Situação de cada história:** `feito` está no código e coberto por teste ou conferido na interface; `parcial` funciona com
limites descritos; `a fazer` ainda não existe.

## Quem usa

**Rafael, professor de inglês (usuário principal).** Dá aulas particulares ou para pequenos grupos, presenciais ou online.
Grava a aula no celular ou na plataforma de vídeo. Não tem tempo de corrigir cada fala depois, mas quer que cada aluno saia
com tarefa sob medida e que a aula seguinte parta do que aconteceu na anterior. Usa computador com impressora ou salva em PDF.

**O aluno (usuário indireto).** Não usa o sistema. Recebe a folha impressa ou em PDF, com a revisão dos próprios erros e
atividades sobre eles.

## Épico 1. Da gravação à transcrição

### US-01. Enviar a gravação da aula (feito)
Como professor, quero enviar o arquivo da aula, para não digitar nada.
- Dado que escolhi um arquivo de áudio ou vídeo aceito, quando envio, então vejo o progresso do envio e a aula entra na fila. (RN-01, RN-02)
- Dado que o arquivo tem formato não aceito ou está vazio, então vejo uma mensagem dizendo o que houve e quais formatos usar. (RN-01)
- Posso arrastar o arquivo para a tela ou escolher no computador.

### US-02. Acompanhar o processamento (feito)
Como professor, quero saber em que pé está a transcrição, para não ficar olhando uma tela parada.
- Vejo "Na fila" ou "Transcrevendo a aula" com um cronômetro, e posso abrir outra página sem perder o trabalho. (RN-05)
- Quando termina, a página abre sozinha na aula pronta. Se falha, vejo o motivo e posso tentar outro arquivo. (RN-06)

### US-03. Ler e ouvir a transcrição (feito)
Como professor, quero ver quem disse o quê e ouvir o trecho, para conferir o que a IA entendeu.
- Cada fala mostra o horário. Ao clicar, o áudio toca daquele ponto. A fala que está tocando fica destacada.
- Posso buscar uma palavra e ver só as falas que a contêm, com o trecho marcado.
- Posso copiar o texto e baixar a transcrição em Markdown.

### US-04. Escolher entre nuvem e processamento local (parcial)
Como professor preocupado com privacidade, quero poder transcrever sem enviar o áudio para fora do computador.
- Em "Opções avançadas" posso escolher o motor local (pyannote com Whisper), se estiver instalado. (RN-08)
- **Limite:** mesmo no motor local, o texto continua indo ao Gemini para criar o material (RN-21). Só o áudio fica na máquina.

## Épico 2. Quem é quem

### US-05. Confirmar o professor e os alunos (feito)
Como professor, quero dizer quais vozes são minhas e quais são de alunos, para que só os alunos recebam folha.
- A tela sugere como professor quem mais fala, ou quem tem "professor", "teacher" ou "tutor" no nome. Eu posso trocar. (RN-10)
- Vejo a porcentagem de fala de cada pessoa. Isso ajuda a perceber uma voz trocada.
- A escolha e os nomes que digito ficam guardados neste navegador para aquela aula. (RN-11)

### US-06. Usar o nome real dos alunos (parcial)
Como professor, quero ver o nome de cada aluno na transcrição e na folha, para entregar a folha certa.
- Posso editar qualquer nome na tela "Quem é quem". A transcrição e as folhas passam a usar o nome novo.
- Se a opção "Descobrir o nome dos alunos" estiver ligada, a IA sugere nomes quando alguém se apresenta ou é chamado pelo nome. (RN-09)
- **Limite:** sem essa pista no texto, os alunos aparecem como "Aluno 1", "Aluno 2". O professor renomeia.

## Épico 3. Atividades individuais

### US-07. Criar atividades para cada aluno (feito)
Como professor, quero atividades baseadas nos erros que cada aluno cometeu, para treinar o que ele precisa.
- Informo o nível da turma (A1 a C2), quantas atividades por aluno (3 a 10) e, se quiser, um foco para a próxima aula. (RN-13 a RN-15)
- Cada aluno recebe um ponto forte, a lista de erros da aula e as atividades. (RN-16 a RN-19)
- Vejo um aviso de que a IA lê só o texto e de que preciso conferir o material. (RN-22)

### US-08. Ver os erros no lugar onde aconteceram (feito)
Como professor, quero ver cada erro marcado na transcrição, para decidir se concordo.
- A forma correta aparece em vermelho acima do trecho, e a explicação ao passar o mouse. (RN-16)
- Só os alunos têm marcação. As falas do professor nunca são marcadas.

### US-09. Conferir o gabarito (feito)
Como professor, quero ver a resposta esperada de cada atividade, para corrigir rápido.
- Na tela, cada atividade mostra a resposta. Na folha impressa para o aluno, a resposta não aparece. (RN-24)

### US-10. Imprimir ou salvar em PDF (feito)
Como professor, quero entregar a folha de cada aluno, para que ele treine fora da aula.
- Posso imprimir a folha de um aluno, todas as folhas, o gabarito ou o plano. Escolho "Salvar como PDF" na janela de impressão. (RN-24, RN-25)
- O arquivo já vem com um nome útil, por exemplo "Atividades, Ana, 22 de novembro de 2026".

### US-11. Gerar de novo (feito)
Como professor, quero criar outro material quando o primeiro não serve, mudando nível, quantidade ou foco.
- "Criar de novo" volta ao formulário. O novo material substitui o anterior. (RN-20)

## Épico 4. Próxima aula

### US-12. Receber um plano de aula (feito)
Como professor, quero um plano que parta do que aconteceu, para não começar do zero.
- O plano traz objetivo, tópicos a retomar, etapas com minutos (aquecimento, apresentação, prática, produção) e tarefa de casa. (RN-19)
- Posso imprimir o plano.

## Épico 5. Fora do escopo atual (a fazer)

Estas histórias foram identificadas e ainda não existem. Estão em ordem de valor para o professor.

### US-13. Editar o material antes de imprimir (a fazer)
Como professor, quero corrigir um enunciado, apagar uma atividade ou trocar uma resposta, porque a IA erra e eu não quero reimprimir do zero.
- Critério: editar texto de enunciado, opções e resposta; remover atividade; a folha impressa reflete a edição.

### US-14. Guardar minhas aulas (a fazer)
Como professor, quero encontrar a aula de semana passada, porque hoje a lista some quando o servidor reinicia. (RN-26)
- Critério: lista de aulas e material continuam após reiniciar; posso excluir uma aula e seus arquivos.

### US-15. Acompanhar a evolução de um aluno (a fazer)
Como professor, quero ver os erros de um aluno ao longo das aulas, para saber se ele aprendeu o passado simples.
- Critério: cadastro de aluno que persiste entre aulas; recorrência de cada tipo de erro por aula.

### US-16. Cadastrar a turma (a fazer)
Como professor, quero cadastrar os alunos uma vez, para que os nomes e o nível já venham preenchidos.
- Critério: turma com alunos e nível; a tela "Quem é quem" sugere o nome da turma por voz (depende de US-15).

### US-17. Entrar com minha conta (a fazer)
Como professor, quero que só eu veja minhas aulas, porque elas contêm a voz e os erros de pessoas.
- Critério: autenticação; aulas separadas por professor. Hoje a aplicação roda só na máquina local e não tem login.

### US-18. Trabalhar com aulas longas ou pesadas (parcial)
Como professor, quero enviar a aula inteira, mesmo com 2 horas ou em vídeo.
- Hoje: o áudio enviado ao Gemini precisa caber em 20 MB. A conversão para Opus 16 kbps cobre cerca de 2 h 50 min, e a opção de remover pausas ajuda. (RN-03)
- A fazer: mensagem antecipada no envio, antes de gastar tempo; divisão da aula quando passar do limite.

### US-19. Escolher o formato da folha (a fazer)
Como professor, quero escolher a identidade da folha (logo da minha escola, nome do curso) e o tamanho do papel.

## Mapa resumido

| Código | História | Situação |
|---|---|---|
| US-01 | Enviar a gravação | feito |
| US-02 | Acompanhar o processamento | feito |
| US-03 | Ler e ouvir a transcrição | feito |
| US-04 | Nuvem ou local | parcial |
| US-05 | Confirmar professor e alunos | feito |
| US-06 | Usar o nome real | parcial |
| US-07 | Criar atividades por aluno | feito |
| US-08 | Ver erros na transcrição | feito |
| US-09 | Conferir o gabarito | feito |
| US-10 | Imprimir ou salvar em PDF | feito |
| US-11 | Gerar de novo | feito |
| US-12 | Plano da próxima aula | feito |
| US-13 | Editar o material | a fazer |
| US-14 | Guardar as aulas | a fazer |
| US-15 | Evolução do aluno | a fazer |
| US-16 | Cadastrar a turma | a fazer |
| US-17 | Conta e privacidade | a fazer |
| US-18 | Aulas longas | parcial |
| US-19 | Formato da folha | a fazer |
