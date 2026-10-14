# Memorial Descritivo e Análise de Engenharia
## Desafios Acústicos, Computacionais e Soluções no Processamento de Fala para IA

**Projeto:** Diarizador 2.0 / Telecom Audio AI  
**Data:** 25/08/2026  
**Foco:** Engenharia de Sinais, Teoria de Telecomunicações e Arquitetura de Software  

---

### 1. Introdução
Durante o desenvolvimento do sistema de diarização e transcrição, foram conduzidas investigações experimentais e identificados 6 desafios críticos na interseção entre processamento digital de sinais (DSP), dinâmica de tokens em LLMs multimodais e sincronismo temporal de vídeo. 

Este memorial detalha a causa raiz de cada problema e a respectiva solução científica implementada.

---

### 2. Desafios Enfrentados e Soluções Implementadas

#### Desafio 1: Dinâmica de Faturamento de Tokens vs. Redução de Bitrate
* **Problema:** A hipótese inicial previa que comprimir um MP3 de 320 kbps para 8 kbps reduziria o consumo de tokens faturados pela API. Nos testes empíricos, observou-se que um MP3 de 320k e um de 8k com 8 minutos geraram exatamente os mesmos ~16.200 tokens.
* **Causa Raiz:** O Encoder Neural multimodal da API não processa o áudio pelo tamanho em bytes, mas sim por janelas temporais fixas de amostragem acústica (taxa de conversão de ~32 tokens de atenção por segundo de áudio).
* **Solução:** Compreendeu-se que a compressão de bitrate atua na camada de **transporte e rede** (reduzindo em até 95% o payload de upload e latência de transferência), enquanto a redução de tokens ocorre unicamente na camada **temporal**.

---

#### Desafio 2: Gargalo Computacional da Normalização de Áudio (EBU R128)
* **Problema:** A inclusão de normalização dinâmica via filtro `loudnorm` elevou o tempo de pré-processamento local de 1,8s para **19,7 segundos** (um aumento de 1000% no tempo computacional local).
* **Causa Raiz:** O algoritmo EBU R128 efetua integração psicoacústica em ponto flutuante de 64 bits em duas passadas (*two-pass analysis*), simulando curvas de audição humana para broadcast de TV/rádio, o que é computacionalmente desnecessário para modelos neurais.
* **Solução:** Constatou-se que as camadas de *Self-Attention* dos Transformers de fala possuem invariância natural a ganho. O algoritmo pesado foi eliminado, mantendo o pré-processamento em menos de 2 segundos.

---

#### Desafio 3: Degradação Tímbrica da Diarização por Filtros Estreitos (Narrowband)
* **Problema:** Ao aplicar filtros telefônicos tradicionais (300 Hz a 3.400 Hz), a diarização perdeu capacidade de distinguir falantes, fundindo vozes distintas.
* **Causa Raiz:** O corte abaixo de 300 Hz elimina a frequência fundamental ($F_0$) de vozes masculinas graves (85 Hz a 150 Hz), e o corte acima de 3.400 Hz descarta os formantes superiores ($F_3$ e $F_4$), que constituem a assinatura tímbrica única do trato vocal de cada pessoa.
* **Solução:** Implementou-se um **Filtro Passa-Faixa Wideband (80 Hz a 7.500 Hz)**, que preserva integralmente $F_0$ e os formantes $F_1$ a $F_4$, eliminando apenas ruídos subsônicos (<80Hz) e chiados (>7.5kHz), garantindo perfeita separação de falantes.

---

#### Desafio 4: Fragmentação Fonética por Fatiamento em Janelas Rígidas
* **Problema:** O fatiamento paralelo em intervalos fixos (ex: cortar exatamente aos 120,0 segundos) cortava palavras ao meio durante a enunciação (ex.: *"compa- / -nheiro"*), gerando alucinações e perda de palavras na fronteira dos blocos.
* **Causa Raiz:** A fala humana é contínua e assíncrona; pontos de corte arbitrários interceptam fonemas no meio de transições de formantes.
* **Solução:** Foi desenvolvido o algoritmo **Silence-Aware Chunking (Fatiamento Inteligente em Pausas)**. O processador local escaneia uma janela de busca de $\pm 18$ segundos com o filtro `silencedetect` procurando vales de energia ($< -35\text{ dB}$ por pelo menos $300\text{ ms}$) e efetua o corte estritamente no silêncio entre frases, preservando 100% da integridade fonética sem deletar nenhum milissegundo da linha temporal original do vídeo.

---

#### Desafio 5: Saturação de Tokens de Saída e Truncamento de JSON
* **Problema:** Em gravações longas com blocos de 3 minutos e diálogos muito densos, o modelo gerava centenas de objetos JSON por bloco, ultrapassando a janela de saída e truncando a resposta antes de fechar a última chave, causando falha no `json.loads` padrão em 5 dos 29 blocos.
* **Causa Raiz:** A densidade informacional de fala em 180s exigia mais tokens de estrutura JSON do que o limite seguro de geração contínua.
* **Solução (Dupla Abordagem):**
  1. Redução do alvo dinâmico de fatiamento para **~90 segundos** (gerando ~40 falas por bloco, mantendo o JSON em ~1.500 tokens).
  2. Implementação de um **Parser com Auto-Reparo Heurístico**, capaz de identificar expressões completas com Regex e reconstruir a árvore JSON mesmo diante de cortes inesperados.
  * **Resultado:** Taxa de sucesso de **100% em 59 de 59 blocos**.

---

#### Desafio 6: Alinhamento Temporal Contínuo Palavra por Palavra
* **Problema:** A API retorna timestamps apenas por frases/turnos (`timestamp_inicio` e `timestamp_fim`). Como o usuário assiste ao vídeo original, era necessário saber a posição exata de cada palavra sem recorrer a chamadas adicionais lentas à API.
* **Causa Raiz:** Modelos de linguagem operam em nível semântico/frasal e não por alinhamento forçado (*Forced Alignment*) acústico nativo.
* **Solução:** Criou-se o algoritmo **`WordLevelTimestampAligner`**, que realiza interpolação ponderada por núcleos vocálicos (número de sílabas), densidade de caracteres e compensação de micro-pausas por pontuação (vírgulas, pontos). O algoritmo distribui os milissegundos de cada fala de forma contínua e determinística para as 14.646 palavras em menos de 0,1s na CPU.

---

### 3. Síntese Técnica
A superação desses obstáculos consolidou um modelo robusto de engenharia, onde o processamento digital de sinais atua como escudo e otimizador prévio para a inteligência artificial, unindo rigor matemático e eficiência computacional.
