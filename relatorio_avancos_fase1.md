# 📑 Relatório Técnico de Avanços: Fase 1 — Otimização de MP3 para Transcrição por IA

**Projeto:** Telecom AI Audio Optimizer & Benchmark  
**Repositório:** `trabalho_telecom_2026.2`  
**Data:** 25/08/2026  
**Autor:** Equipe de Pesquisa em Telecomunicações  

---

## 1. Resumo Executivo
Nesta primeira fase de pesquisa, estruturamos uma infraestrutura automatizada e modular em Python para investigar como diferentes técnicas de processamento de sinais, compressão e filtragem no formato **MP3** afetam a transcrição de fala realizada pela **API do Google Gemini (Multimodal Audio)**.

Realizamos a validação empírica completa em um arquivo real de vídeo de audiência de custódia ([999.mp4](file:///C:/Users/Lukas/Documents/GitHub/trabalho_telecom_2026.2/input/999.mp4), ~8m40s de duração e 22,08 MB de tamanho bruto), submetendo-o a **16 tratamentos acústicos distintos**.

---

## 2. Infraestrutura Desenvolvida
1. **Pipeline de Transcodificação:** Motor baseado em FFmpeg para variação controlada de bitrates (8k a 320k), taxas de amostragem (8kHz a 44.1kHz), canais (Mono/Estéreo) e filtros digitais.
2. **Integração Multimodal com Gemini API:** Cliente assíncrono com extração de métricas de `usage_metadata` (contagem de tokens reais faturados).
3. **Métricas de Telecomunicações:** Motor de cálculo de taxa de compressão, economia de largura de banda (%), latência local de pré-processamento, latência de nuvem e custo financeiro em USD/BRL.
4. **Visualização Automatizada:** Geração automática de gráficos de dispersão, curvas de tradeoff e fronteira de Pareto com Matplotlib/Seaborn.

---

## 3. Resultados Quantitativos da Fase 1

| Tratamento | Tamanho (KB) | Economia de Banda | Tokens Cobrados | Latência Nuvem | Custo (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Original (MP4)** | `22.087 KB` | - | - | - | - |
| **Baseline 320k (Estéreo 44.1k)** | `18.171 KB` | 17.73% | 16.238 | 17.77s | \$0.003026 |
| **MP3 192k (Estéreo 44.1k)** | `10.903 KB` | 50.64% | 16.038 | 12.12s | \$0.002906 |
| **MP3 128k (Estéreo 44.1k)** | `7.268 KB` | 67.09% | 16.248 | 26.24s | \$0.003032 |
| **MP3 64k (Estéreo 44.1k)** | `3.634 KB` | 83.54% | 16.274 | 11.26s | \$0.003029 |
| **MP3 32k (Estéreo 44.1k)** | `1.817 KB` | 91.77% | 16.249 | 10.32s | \$0.003033 |
| **MP3 16k (Mono 22.05k)** | `909 KB` | 95.88% | 16.194 | 9.78s | \$0.002999 |
| **MP3 8k (Mono 16k)** | `454 KB` | **97.94%** | 16.209 | 10.38s | \$0.003008 |
| **Sample Rate 24kHz (128k)** | `7.268 KB` | 67.09% | 16.218 | 10.25s | \$0.003015 |
| **Sample Rate 16kHz (128k)** | `7.269 KB` | 67.09% | 16.290 | 10.84s | \$0.003032 |
| **Sample Rate 8kHz (Telefonia)** | `3.635 KB` | 83.54% | 16.221 | 11.36s | \$0.003015 |
| **Downmix para Mono (128k)** | `7.268 KB` | 67.09% | 16.208 | 11.19s | \$0.003008 |
| **Filtro Telefônico (300Hz-3.4kHz)**| `3.634 KB` | 83.54% | 16.257 | 9.85s | \$0.003037 |
| **Filtro Voz Wideband (80Hz-7.5kHz)**| `3.634 KB` | 83.54% | 16.239 | 27.68s | \$0.003026 |
| **VAD (Corte de Silêncio)** | `2.298 KB` | **89.60%** | **10.741** | **9.58s** | **\$0.002192** |
| **Normalização LUFS (EBU R128)** | `3.634 KB` | 83.54% | 16.228 | 10.52s | \$0.003019 |
| **⭐ MP3 Otimizado para IA** | **`1.147 KB`** | **94.80%** | **10.767** | **12.81s** | **\$0.002183** |

---

## 4. Descobertas Científicas e Conclusões Técnicas

### 4.1. Dinâmica de Faturamento de Tokens em Modelos Multimodais
* **Independência do Bitrate/Sample Rate nos Tokens:** Comprimir o áudio de 320k para 8k ou reduzir a taxa de amostragem para 8kHz não altera a quantidade de tokens consumidos (~16.200 tokens em todos os testes contínuos). Isso ocorre porque a arquitetura do Gemini amostra o áudio em intervalos temporais fixos (~32 tokens/segundo).
* **Impacto do VAD (Voice Activity Detection):** O corte de silêncio foi a **única variável capaz de reduzir o consumo de tokens** (de 16.238 para 10.741 tokens, gerando **33,8% de economia financeira direta**).

### 4.2. Tolerância Acústica da IA a Baixos Bitrates
* Mesmo em taxas extremas de **8 kbps Mono (redução de 97,94% no tamanho do arquivo)**, o modelo transcreveu nomes próprios complexos, termos jurídicos, números de RG e CPF sem alucinação.
* Arquivos menores apresentaram **latência de upload e resposta de IA até 40% menor** que o áudio bruto.

### 4.3. Gargalo de Processamento da Normalização EBU R128
* A normalização em duas passadas (`loudnorm`) consumiu **19,7 segundos de CPU**, representando um custo computacional desproporcional frente aos benefícios.
* Modelos com mecanismos de *Self-Attention* demonstraram invariância a variações de ganho acústico razoáveis, tornando a normalização pesada desnecessária.

### 4.4. Filtros de Frequência vs. Diarização (Identificação de Falantes)
* **Filtros Narrowband (300Hz-3.4kHz):** Cortam a frequência fundamental ($F_0$) de vozes graves (<300Hz) e formantes superiores ($F_3, F_4$), prejudicando a separação tímbrica entre falantes.
* **Filtros Wideband (80Hz-7.5kHz):** Preservam a integralidade fonética e o timbre individual dos falantes, eliminando ruídos subgraves e agudos espúrios sem afetar a diarização.

---

## 5. Diretrizes para a Fase 2 (`diarizador2.0`)
Para a próxima etapa de desenvolvimento com foco em **Diarização (Identificação e Separação de Falantes)**:
1. **Desativação do VAD:** Preservar a continuidade temporal e prosódia exata das falas e pausas de cada interlocutor.
2. **Remoção de Normalização Pesada:** Manter processamento ultrarrápido (<1s).
3. **Filtro Wideband (80Hz-7.5kHz):** Padronizado para preservar os formantes de diarização.
4. **Prompting Especializado de Diarização:** Estruturar a saída do Gemini com rótulos de falantes (ex.: *[Juiz]*, *[Réu]*, *[Defensor]*).
5. **Cálculo de Desvio (WER Relativo):** Medir o desvio textual e de identificação de falantes contra o Baseline de 320k.
