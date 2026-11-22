/**
 * Telecom 2026.2 — Frontend Controller
 * Áudio, Diarização de Falantes e Métricas com Gemini
 */

const STATE = {
  reports: [],
  currentReportId: null,
  currentReport: null,
  currentWords: null,
  systemStatus: null,
  activeTab: 'diarizacao',
  transcriptViewMode: 'speakers',
  reportViewerMode: 'md',
  activeReportViewerData: null,
  currentTime: 0,
  duration: 0,
  isPlaying: false,
  isRealAudio: false,
  playbackRate: 1.0,
  simTimer: null,
  lastActiveSegmentIndex: -1,
  speakerColors: {},
  charts: {}
};

const COLOR_CLASSES = [
  'speaker-color-0',
  'speaker-color-1',
  'speaker-color-2',
  'speaker-color-3',
  'speaker-color-4',
  'speaker-color-5'
];

// Inicialização
document.addEventListener('DOMContentLoaded', async () => {
  setupAudioListeners();
  await loadSystemStatus();
  await loadReports();
  await loadBenchmarkMatrices();
  setupKeyboardShortcuts();
});

// ==========================================
// STATUS DO SISTEMA
// ==========================================
async function loadSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    STATE.systemStatus = data;

    const geminiDot = document.getElementById('geminiDot');
    const geminiText = document.getElementById('geminiText');
    if (data.has_gemini_key) {
      geminiDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
      geminiText.textContent = `Gemini: ${data.gemini_model}`;
    } else {
      geminiDot.className = 'w-2 h-2 rounded-full bg-amber-400';
      geminiText.textContent = 'Gemini: Sem API Key (.env)';
    }

    const ffmpegDot = document.getElementById('ffmpegDot');
    const ffmpegText = document.getElementById('ffmpegText');
    if (data.has_ffmpeg) {
      ffmpegDot.className = 'w-2 h-2 rounded-full bg-emerald-400';
      ffmpegText.textContent = 'FFmpeg: Ativo';
    } else {
      ffmpegDot.className = 'w-2 h-2 rounded-full bg-amber-400';
      ffmpegText.textContent = 'FFmpeg: Ausente';
    }
  } catch (err) {
    console.error('Falha ao carregar status:', err);
  }
}

// ==========================================
// NAVEGAÇÃO ENTRE ABAS
// ==========================================
function switchTab(tabName) {
  STATE.activeTab = tabName;
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-item').forEach(el => {
    el.className = 'nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-800/50';
  });

  const activeContent = document.getElementById(`tab-${tabName}`);
  if (activeContent) activeContent.classList.remove('hidden');

  const activeNav = document.getElementById(`nav-${tabName}`);
  if (activeNav) {
    activeNav.className = 'nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all bg-purple-600/15 text-purple-300 border border-purple-500/30';
  }

  if (tabName === 'metricas') {
    renderCharts();
  }
}

// ==========================================
// CARREGAMENTO DE RELATÓRIOS
// ==========================================
async function loadReports() {
  try {
    const res = await fetch('/api/reports');
    STATE.reports = await res.json();

    const select = document.getElementById('reportSelect');
    const quickList = document.getElementById('quickReportsList');
    const fullTable = document.getElementById('fullReportsTable');

    select.innerHTML = '';
    quickList.innerHTML = '';
    if (fullTable) fullTable.innerHTML = '';

    if (STATE.reports.length === 0) {
      select.innerHTML = '<option value="">Nenhum relatório encontrado</option>';
      quickList.innerHTML = '<div class="text-xs text-slate-500 px-3 py-2">Nenhum relatório disponível.</div>';
      return;
    }

    STATE.reports.forEach((rep, idx) => {
      // Option no select
      const opt = document.createElement('option');
      opt.value = rep.id;
      const vadTag = rep.vad_aplicado ? `[VAD -${rep.economia_silencio_pct}%]` : '[SEM VAD]';
      opt.textContent = `${rep.arquivo} (${Math.round(rep.duracao_original_segundos)}s) ${vadTag}`;
      select.appendChild(opt);

      // Item na barra lateral
      const quickItem = document.createElement('button');
      quickItem.className = 'w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 transition-all flex items-center justify-between group';
      quickItem.onclick = () => {
        select.value = rep.id;
        loadSelectedReport();
        switchTab('diarizacao');
      };
      quickItem.innerHTML = `
        <span class="truncate max-w-[130px] group-hover:text-purple-300">${rep.arquivo}</span>
        <span class="text-[10px] text-slate-500 font-mono">${rep.codec}</span>
      `;
      quickList.appendChild(quickItem);

      // Card na Central de Relatórios
      if (fullTable) {
        const card = document.createElement('div');
        card.className = 'p-3.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-purple-500/40 cursor-pointer transition-all space-y-2';
        card.onclick = () => viewReportInCentral(rep.id);
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-200 truncate">${rep.arquivo}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-mono ${rep.vad_aplicado ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}">${rep.codec}</span>
          </div>
          <div class="text-[11px] text-slate-400 flex justify-between">
            <span>Duração: ${Math.round(rep.duracao_original_segundos)}s</span>
            <span>Turnos: ${rep.total_turnos_fala}</span>
          </div>
          <div class="text-[10px] text-purple-400 flex justify-between pt-1 border-t border-slate-800/80">
            <span>Tokens: ${rep.metricas_tokens?.total_tokens?.toLocaleString() || '--'}</span>
            <span>Custo: US$ ${rep.custo_estimado?.custo_usd || '--'}</span>
          </div>
        `;
        fullTable.appendChild(card);
      }
    });

    // Seleciona o primeiro relatório
    if (STATE.reports.length > 0) {
      select.value = STATE.reports[0].id;
      await loadSelectedReport();
      viewReportInCentral(STATE.reports[0].id);
    }
  } catch (err) {
    console.error('Falha ao listar relatórios:', err);
  }
}

async function loadSelectedReport() {
  const select = document.getElementById('reportSelect');
  const reportId = select.value;
  if (!reportId) return;

  STATE.currentReportId = reportId;
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(reportId)}`);
    const data = await res.json();
    STATE.currentReport = data;
    STATE.duration = data.duracao_original_segundos || 0;

    // Reseta estado de reprodução
    pauseAudio();
    STATE.currentTime = 0;
    STATE.lastActiveSegmentIndex = -1;

    // Atualiza badges de métricas
    updateMetricsCards(data);

    // Configura o Player de Áudio (real ou simulado)
    setupAudioSource(data);

    // Carrega alinhamento palavra por palavra se disponível
    await loadWordAlignment(reportId);

    // Renderiza os segmentos
    renderTranscriptSegments(data.segmentos || []);

    // Renderiza linha do tempo VAD
    renderVadTimelineBar(data);

  } catch (err) {
    console.error('Erro ao abrir relatório:', err);
  }
}

// ==========================================
// MÉTRICAS E CARDS
// ==========================================
function updateMetricsCards(data) {
  document.getElementById('metricOriginalDuration').textContent = `${formatMinutes(data.duracao_original_segundos)}`;
  const vadBadge = document.getElementById('metricVadBadge');
  const compactDur = document.getElementById('metricCompactDuration');
  const savedPct = document.getElementById('metricSavedPct');
  const savedSec = document.getElementById('metricSavedSec');

  if (data.vad_aplicado) {
    vadBadge.className = 'text-[10px] px-1.5 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
    vadBadge.textContent = 'VAD ATIVO';
    compactDur.textContent = `VAD: ${formatMinutes(data.duracao_compactada_segundos)}`;
    savedPct.textContent = `-${data.economia_silencio_pct}%`;
    savedSec.textContent = `-${Math.round(data.economia_silencio_segundos)}s de silêncio`;
  } else {
    vadBadge.className = 'text-[10px] px-1.5 py-0.5 rounded font-bold bg-slate-800 text-slate-400 border border-slate-700';
    vadBadge.textContent = 'SEM VAD';
    compactDur.textContent = 'Áudio integral';
    savedPct.textContent = '0%';
    savedSec.textContent = 'Sem corte de pausas';
  }

  const tokens = data.metricas_tokens || {};
  document.getElementById('metricTotalTokens').textContent = (tokens.total_tokens || 0).toLocaleString();
  document.getElementById('metricTokensSplit').textContent =
    `Áudio: ${(tokens.prompt_tokens_audio || 0).toLocaleString()} | Texto: ${(tokens.candidate_tokens_texto || 0).toLocaleString()}`;

  const cost = data.custo_estimado || {};
  document.getElementById('metricCostUsd').textContent = `US$ ${cost.custo_usd ?? '--'}`;
  document.getElementById('metricCostBrl').textContent = `~ R$ ${cost.custo_brl ?? '--'}`;

  document.getElementById('metricTurnsCount').textContent = data.total_turnos_fala || (data.segmentos?.length ?? '--');
  document.getElementById('metricCloudTime').textContent = `Nuvem: ${data.tempo_processamento_nuvem_segundos ?? '--'}s`;

  document.getElementById('totalDurationDisplay').textContent = formatSeconds(data.duracao_original_segundos || 0);
  const timeSlider = document.getElementById('timeSlider');
  timeSlider.max = data.duracao_original_segundos || 100;
  timeSlider.value = 0;
}

// ==========================================
// PLAYER DE ÁUDIO / VÍDEO & SINCRONIZAÇÃO
// ==========================================
function setupAudioListeners() {
  const audio = document.getElementById('audioElement');
  audio.addEventListener('timeupdate', () => {
    if (STATE.isRealAudio) {
      onTimeProgress(audio.currentTime);
    }
  });
  audio.addEventListener('ended', () => {
    pauseAudio();
    STATE.currentTime = 0;
    onTimeProgress(0);
  });
}

function setupAudioSource(data) {
  const audio = document.getElementById('audioElement');
  const notice = document.getElementById('playerStatusNotice');

  if (data.media_url) {
    STATE.isRealAudio = true;
    audio.src = data.media_url;
    audio.load();
    notice.textContent = 'Áudio Real Carregado (input/output)';
    notice.className = 'text-emerald-400 text-[11px] font-sans';
  } else {
    STATE.isRealAudio = false;
    audio.removeAttribute('src');
    notice.textContent = 'Simulador de Áudio Sincronizado (Pesquisa)';
    notice.className = 'text-indigo-400 text-[11px] font-sans';
  }
}

function togglePlayPause() {
  if (STATE.isPlaying) {
    pauseAudio();
  } else {
    playAudio();
  }
}

function playAudio() {
  STATE.isPlaying = true;
  updatePlayButtonIcon(true);

  if (STATE.isRealAudio) {
    const audio = document.getElementById('audioElement');
    audio.playbackRate = STATE.playbackRate;
    audio.play().catch(e => console.warn('Erro ao reproduzir áudio real:', e));
  } else {
    // Simulador de áudio em tempo real
    if (STATE.simTimer) clearInterval(STATE.simTimer);
    const intervalMs = 100;
    STATE.simTimer = setInterval(() => {
      const step = (intervalMs / 1000) * STATE.playbackRate;
      let nextTime = STATE.currentTime + step;
      if (nextTime >= STATE.duration) {
        nextTime = STATE.duration;
        pauseAudio();
      }
      onTimeProgress(nextTime);
    }, intervalMs);
  }
}

function pauseAudio() {
  STATE.isPlaying = false;
  updatePlayButtonIcon(false);

  if (STATE.isRealAudio) {
    const audio = document.getElementById('audioElement');
    audio.pause();
  }
  if (STATE.simTimer) {
    clearInterval(STATE.simTimer);
    STATE.simTimer = null;
  }
}

function updatePlayButtonIcon(isPlaying) {
  const icon = document.getElementById('playIcon');
  if (isPlaying) {
    icon.setAttribute('data-lucide', 'pause');
  } else {
    icon.setAttribute('data-lucide', 'play');
  }
  lucide.createIcons();
}

function seekToSeconds(sec, andPlay = true) {
  STATE.currentTime = Math.max(0, Math.min(sec, STATE.duration));
  if (STATE.isRealAudio) {
    const audio = document.getElementById('audioElement');
    audio.currentTime = STATE.currentTime;
  }
  onTimeProgress(STATE.currentTime);
  if (andPlay && !STATE.isPlaying) {
    playAudio();
  }
}

function seekRelative(deltaSec) {
  seekToSeconds(STATE.currentTime + deltaSec, STATE.isPlaying);
}

function onSliderSeek(val) {
  seekToSeconds(parseFloat(val), STATE.isPlaying);
}

function changePlaybackRate(rate) {
  STATE.playbackRate = parseFloat(rate);
  if (STATE.isRealAudio) {
    document.getElementById('audioElement').playbackRate = STATE.playbackRate;
  }
}

function onTimeProgress(currSec) {
  STATE.currentTime = currSec;
  document.getElementById('currentTimeDisplay').textContent = formatSeconds(currSec);
  document.getElementById('timeSlider').value = currSec;

  // Sincroniza segmento de falante ativo
  synchronizeTranscriptTurn(currSec);

  // Sincroniza palavra ativa se visão palavra estiver aberta
  if (STATE.transcriptViewMode === 'words') {
    synchronizeWords(currSec);
  }
}

function synchronizeTranscriptTurn(currSec) {
  const segments = STATE.currentReport?.segmentos || [];
  let activeIdx = -1;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    if (currSec >= seg.segundos_inicio && currSec <= seg.segundos_fim) {
      activeIdx = i;
      break;
    }
  }

  if (activeIdx !== STATE.lastActiveSegmentIndex) {
    if (STATE.lastActiveSegmentIndex !== -1) {
      const prevEl = document.getElementById(`seg-${STATE.lastActiveSegmentIndex}`);
      if (prevEl) prevEl.classList.remove('active-turn');
    }

    if (activeIdx !== -1) {
      const currEl = document.getElementById(`seg-${activeIdx}`);
      if (currEl) {
        currEl.classList.add('active-turn');
        currEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
    STATE.lastActiveSegmentIndex = activeIdx;
  }
}

function synchronizeWords(currSec) {
  const words = STATE.currentWords?.palavras || [];
  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    const el = document.getElementById(`word-${i}`);
    if (el) {
      if (currSec >= w.segundos_inicio && currSec <= w.segundos_fim) {
        el.classList.add('active-word');
      } else {
        el.classList.remove('active-word');
      }
    }
  }
}

// ==========================================
// RENDERIZAÇÃO DA TRANSCRIÇÃO
// ==========================================
function getSpeakerColorClass(speaker) {
  if (!STATE.speakerColors[speaker]) {
    const idx = Object.keys(STATE.speakerColors).length % COLOR_CLASSES.length;
    STATE.speakerColors[speaker] = COLOR_CLASSES[idx];
  }
  return STATE.speakerColors[speaker];
}

function renderTranscriptSegments(segments) {
  const container = document.getElementById('speakersContainer');
  container.innerHTML = '';

  if (!segments || segments.length === 0) {
    container.innerHTML = '<div class="text-center py-10 text-slate-500">Nenhuma fala encontrada no relatório.</div>';
    return;
  }

  segments.forEach((seg, idx) => {
    const card = document.createElement('div');
    card.id = `seg-${idx}`;
    card.className = 'transcript-turn p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 cursor-pointer space-y-2';
    card.onclick = (e) => {
      // Evita disparar seek se clicar no botão de renomear
      if (e.target.closest('.no-seek')) return;
      seekToSeconds(seg.segundos_inicio, true);
    };

    const colorClass = getSpeakerColorClass(seg.quemfala);
    const speakerDisplayName = seg.falante_identificado
      ? `${seg.falante_identificado} (${seg.quemfala})`
      : seg.quemfala;

    card.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center gap-2">
          <!-- Speaker Badge -->
          <span class="px-2.5 py-1 rounded-lg border text-xs font-semibold ${colorClass} flex items-center gap-1.5">
            <i data-lucide="user" class="w-3 h-3"></i>
            <span>${speakerDisplayName}</span>
          </span>
          <!-- Rename Button -->
          <button onclick="openRenameModal('${escapeJsString(seg.quemfala)}')" class="no-seek text-slate-500 hover:text-slate-300 p-1 rounded" title="Renomear falante">
            <i data-lucide="edit-2" class="w-3 h-3"></i>
          </button>
        </div>

        <!-- Timestamp Button -->
        <button class="no-seek font-mono text-[11px] text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 px-2 py-0.5 rounded border border-purple-500/30 flex items-center gap-1">
          <i data-lucide="clock" class="w-3 h-3"></i>
          <span>${seg.timestamp || `${formatSeconds(seg.segundos_inicio)} - ${formatSeconds(seg.segundos_fim)}`}</span>
        </button>
      </div>

      <!-- Texto da fala -->
      <p class="text-sm text-slate-200 leading-relaxed font-normal">${seg.textodefala}</p>
    `;

    container.appendChild(card);
  });

  lucide.createIcons();
}

function renderVadTimelineBar(data) {
  const bar = document.getElementById('vadTimelineBar');
  const indicator = document.getElementById('vadSavedIndicator');
  bar.innerHTML = '';

  if (!data.vad_aplicado) {
    bar.innerHTML = '<div class="w-full h-full bg-purple-600/80"></div>';
    indicator.textContent = 'Áudio integral (sem VAD)';
    return;
  }

  indicator.textContent = `Economia VAD: ${data.economia_silencio_pct}% (${Math.round(data.economia_silencio_segundos)}s)`;

  // Renderiza blocos com base no mapa ou segmentos
  const segments = data.segmentos || [];
  const totalSec = data.duracao_original_segundos || 1;

  segments.forEach(seg => {
    const leftPct = (seg.segundos_inicio / totalSec) * 100;
    const widthPct = Math.max(0.5, ((seg.segundos_fim - seg.segundos_inicio) / totalSec) * 100);

    const chunk = document.createElement('div');
    chunk.className = 'absolute h-full bg-purple-500 hover:bg-purple-400 transition-all cursor-pointer';
    chunk.style.left = `${leftPct}%`;
    chunk.style.width = `${widthPct}%`;
    chunk.title = `${seg.quemfala}: ${seg.timestamp}`;
    chunk.onclick = () => seekToSeconds(seg.segundos_inicio, true);
    bar.appendChild(chunk);
  });
}

function filterTranscript(query) {
  const q = query.toLowerCase().trim();
  const segments = STATE.currentReport?.segmentos || [];

  segments.forEach((seg, idx) => {
    const el = document.getElementById(`seg-${idx}`);
    if (!el) return;
    const matchText = seg.textodefala.toLowerCase().includes(q);
    const matchSpeaker = (seg.quemfala.toLowerCase().includes(q) || (seg.falante_identificado || '').toLowerCase().includes(q));
    if (matchText || matchSpeaker || q === '') {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });
}

// ==========================================
// VISÃO PALAVRA POR PALAVRA (WORD-LEVEL)
// ==========================================
async function loadWordAlignment(reportId) {
  const container = document.getElementById('wordsChipsList');
  const countBadge = document.getElementById('wordsCountBadge');
  container.innerHTML = '';

  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(reportId)}/words`);
    if (!res.ok) {
      STATE.currentWords = null;
      countBadge.textContent = 'Alinhamento palavra por palavra indisponível para este relatório.';
      return;
    }
    const data = await res.json();
    STATE.currentWords = data;
    countBadge.textContent = `Total de palavras alinhadas: ${data.total_palavras || data.palavras?.length || 0}`;

    const words = data.palavras || [];
    words.forEach((w, idx) => {
      const chip = document.createElement('span');
      chip.id = `word-${idx}`;
      chip.className = 'word-chip inline-block text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono';
      chip.textContent = w.palavra;
      chip.title = `[${w.timestamp || `${w.segundos_inicio}s`}] ${w.quemfala || ''}`;
      chip.onclick = () => seekToSeconds(w.segundos_inicio, true);
      container.appendChild(chip);
    });
  } catch (err) {
    STATE.currentWords = null;
    countBadge.textContent = 'Alinhamento por palavra não gerado.';
  }
}

function setTranscriptViewMode(mode) {
  STATE.transcriptViewMode = mode;
  const btnSpeakers = document.getElementById('viewModeSpeakers');
  const btnWords = document.getElementById('viewModeWords');
  const speakersDiv = document.getElementById('speakersContainer');
  const wordsDiv = document.getElementById('wordsContainer');

  if (mode === 'speakers') {
    btnSpeakers.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 text-white transition-all flex items-center gap-1.5';
    btnWords.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition-all flex items-center gap-1.5';
    speakersDiv.classList.remove('hidden');
    wordsDiv.classList.add('hidden');
  } else {
    btnWords.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 text-white transition-all flex items-center gap-1.5';
    btnSpeakers.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition-all flex items-center gap-1.5';
    speakersDiv.classList.add('hidden');
    wordsDiv.classList.remove('hidden');
  }
}

// ==========================================
// CENTRAL DE RELATÓRIOS & PREVIEW
// ==========================================
async function viewReportInCentral(reportId) {
  document.getElementById('reportViewerTitle').textContent = `Relatório: ${reportId}`;
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(reportId)}`);
    const data = await res.json();
    STATE.activeReportViewerData = data;

    // Busca Markdown
    const resMd = await fetch(`/api/reports/${encodeURIComponent(reportId)}/markdown`);
    let mdText = '';
    if (resMd.ok) {
      const mdJson = await resMd.json();
      mdText = mdJson.markdown;
    }

    document.getElementById('reportMarkdownViewer').innerHTML = mdText
      ? marked.parse(mdText)
      : '<p class="text-slate-500">Markdown não disponível para este relatório.</p>';

    document.getElementById('reportJsonViewer').textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error('Falha ao abrir detalhes do relatório:', err);
  }
}

function setReportViewMode(mode) {
  STATE.reportViewerMode = mode;
  const btnMd = document.getElementById('btnReportMd');
  const btnJson = document.getElementById('btnReportJson');
  const mdView = document.getElementById('reportMarkdownViewer');
  const jsonView = document.getElementById('reportJsonViewer');

  if (mode === 'md') {
    btnMd.className = 'px-2.5 py-1 text-xs font-semibold rounded bg-purple-600 text-white';
    btnJson.className = 'px-2.5 py-1 text-xs font-semibold rounded text-slate-400 hover:text-white';
    mdView.classList.remove('hidden');
    jsonView.classList.add('hidden');
  } else {
    btnJson.className = 'px-2.5 py-1 text-xs font-semibold rounded bg-purple-600 text-white';
    btnMd.className = 'px-2.5 py-1 text-xs font-semibold rounded text-slate-400 hover:text-white';
    mdView.classList.add('hidden');
    jsonView.classList.remove('hidden');
  }
}

// ==========================================
// EXPORTAÇÕES
// ==========================================
function exportTranscriptTxt() {
  if (!STATE.currentReport) return;
  const segments = STATE.currentReport.segmentos || [];
  let txt = `RELATÓRIO DE TRANSCRIÇÃO - TELECOM 2026.2\n`;
  txt += `Arquivo: ${STATE.currentReport.arquivo}\n`;
  txt += `Codec: ${STATE.currentReport.codec} | VAD: ${STATE.currentReport.vad_aplicado ? 'Sim' : 'Não'}\n\n`;

  segments.forEach(seg => {
    const speaker = seg.falante_identificado ? `${seg.falante_identificado} (${seg.quemfala})` : seg.quemfala;
    txt += `[${seg.timestamp}] ${speaker}:\n${seg.textodefala}\n\n`;
  });

  navigator.clipboard.writeText(txt).then(() => {
    alert('Transcrição copiada para a área de transferência com sucesso!');
  });
}

function downloadActiveReportJson() {
  if (!STATE.currentReport) return;
  const blob = new Blob([JSON.stringify(STATE.currentReport, null, 2)], { type: 'application/json' });
  downloadBlob(blob, STATE.currentReportId || 'relatorio_diarizacao.json');
}

async function downloadActiveReportMd() {
  if (!STATE.currentReportId) return;
  const res = await fetch(`/api/reports/${encodeURIComponent(STATE.currentReportId)}/markdown`);
  if (res.ok) {
    const data = await res.json();
    const blob = new Blob([data.markdown], { type: 'text/markdown' });
    downloadBlob(blob, STATE.currentReportId.replace('.json', '.md'));
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ==========================================
// RENOMEAR FALANTE
// ==========================================
let targetOldSpeaker = '';
function openRenameModal(speaker) {
  targetOldSpeaker = speaker;
  document.getElementById('renameOldSpeaker').value = speaker;
  document.getElementById('renameNewSpeaker').value = '';
  document.getElementById('modalRenameSpeaker').classList.remove('hidden');
  document.getElementById('renameNewSpeaker').focus();
}

function closeRenameModal() {
  document.getElementById('modalRenameSpeaker').classList.add('hidden');
}

async function saveRenameSpeaker() {
  const newName = document.getElementById('renameNewSpeaker').value.trim();
  if (!newName) return;

  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(STATE.currentReportId)}/rename-speaker`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report_file: STATE.currentReportId,
        old_speaker: targetOldSpeaker,
        new_speaker: newName
      })
    });
    if (res.ok) {
      closeRenameModal();
      await loadSelectedReport();
    } else {
      alert('Falha ao renomear falante.');
    }
  } catch (err) {
    console.error(err);
  }
}

// ==========================================
// BENCHMARK MATRIZES
// ==========================================
async function loadBenchmarkMatrices() {
  const container = document.getElementById('benchmarkMatricesContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/benchmark/matrices');
    const data = await res.json();

    container.innerHTML = '';
    for (const [suiteName, treatments] of Object.entries(data)) {
      const suiteCard = document.createElement('div');
      suiteCard.className = 'p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3';
      suiteCard.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 class="text-sm font-bold text-purple-300 uppercase tracking-wider">Suíte: ${suiteName} (${treatments.length} tratamentos)</h3>
          <span class="text-xs text-slate-500 font-mono">telecom.experiments.${suiteName}</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left text-slate-300">
            <thead class="text-[11px] text-slate-500 border-b border-slate-800">
              <tr>
                <th class="py-2 pr-3">Tratamento</th>
                <th class="py-2 px-3">Codec</th>
                <th class="py-2 px-3">Bitrate</th>
                <th class="py-2 px-3">Sample Rate</th>
                <th class="py-2 px-3">Canais</th>
                <th class="py-2 px-3">VAD</th>
                <th class="py-2 px-3">Filtros</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono">
              ${treatments.map(t => `
                <tr class="hover:bg-slate-800/40">
                  <td class="py-2 pr-3 font-semibold text-slate-200">${t.label || t.id}</td>
                  <td class="py-2 px-3">${t.codec}</td>
                  <td class="py-2 px-3">${t.bitrate || '--'}</td>
                  <td class="py-2 px-3">${t.sample_rate} Hz</td>
                  <td class="py-2 px-3">${t.channels === 1 ? 'Mono' : 'Estéreo'}</td>
                  <td class="py-2 px-3 ${t.compact_silence ? 'text-emerald-400 font-bold' : 'text-slate-500'}">${t.compact_silence ? 'Sim' : 'Não'}</td>
                  <td class="py-2 px-3 text-slate-400">${t.filters.length > 0 ? t.filters.join(', ') : 'Nenhum'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      container.appendChild(suiteCard);
    }
  } catch (err) {
    console.error('Falha ao carregar matrizes:', err);
  }
}

// ==========================================
// GRÁFICOS (CHART.JS)
// ==========================================
function renderCharts() {
  if (STATE.reports.length === 0) return;

  const labels = STATE.reports.map(r => r.arquivo.replace('.mp4', '').replace('.mp3', ''));
  const vadPct = STATE.reports.map(r => r.economia_silencio_pct || 0);
  const audioTokens = STATE.reports.map(r => r.metricas_tokens?.prompt_tokens_audio || 0);
  const textTokens = STATE.reports.map(r => r.metricas_tokens?.candidate_tokens_texto || 0);
  const costsBrl = STATE.reports.map(r => r.custo_estimado?.custo_brl || 0);

  // Destrói gráficos anteriores se existirem
  if (STATE.charts.vad) STATE.charts.vad.destroy();
  if (STATE.charts.tokens) STATE.charts.tokens.destroy();
  if (STATE.charts.costs) STATE.charts.costs.destroy();

  // 1. Gráfico Economia VAD
  const ctxVad = document.getElementById('chartVadEconomy').getContext('2d');
  STATE.charts.vad = new Chart(ctxVad, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Economia VAD (%)',
        data: vadPct,
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, ticks: { color: '#94A3B8' }, grid: { color: '#1E293B' } },
        x: { ticks: { color: '#94A3B8' }, grid: { display: false } }
      }
    }
  });

  // 2. Gráfico Tokens
  const ctxTokens = document.getElementById('chartTokens').getContext('2d');
  STATE.charts.tokens = new Chart(ctxTokens, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Áudio (Prompt)',
          data: audioTokens,
          backgroundColor: 'rgba(139, 92, 246, 0.8)',
          borderRadius: 6
        },
        {
          label: 'Texto (Resposta)',
          data: textTokens,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#CBD5E1', font: { size: 10 } } }
      },
      scales: {
        y: { beginAtZero: true, ticks: { color: '#94A3B8' }, grid: { color: '#1E293B' } },
        x: { ticks: { color: '#94A3B8' }, grid: { display: false } }
      }
    }
  });

  // 3. Gráfico Custos
  const ctxCosts = document.getElementById('chartCosts').getContext('2d');
  STATE.charts.costs = new Chart(ctxCosts, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Custo Estimado (R$)',
        data: costsBrl,
        backgroundColor: 'rgba(245, 158, 11, 0.7)',
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { color: '#94A3B8' }, grid: { color: '#1E293B' } },
        x: { ticks: { color: '#94A3B8' }, grid: { display: false } }
      }
    }
  });
}

// ==========================================
// MODAL NOVA DIARIZAÇÃO & EXECUÇÃO
// ==========================================
async function openNewDiarizeModal() {
  const modal = document.getElementById('modalNewDiarize');
  modal.classList.remove('hidden');

  // Carrega arquivos disponíveis em input/
  try {
    const res = await fetch('/api/inputs');
    const files = await res.json();
    const select = document.getElementById('modalFileInput');
    select.innerHTML = '';

    if (files.length === 0) {
      select.innerHTML = '<option value="">Nenhum arquivo em input/ (faça upload ao lado)</option>';
    } else {
      files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.name;
        opt.textContent = `${f.name} (${f.size_mb} MB)`;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error('Falha ao listar inputs:', err);
  }
}

function closeNewDiarizeModal() {
  document.getElementById('modalNewDiarize').classList.add('hidden');
}

async function uploadAudioFile(inputEl) {
  if (!inputEl.files || inputEl.files.length === 0) return;
  const file = inputEl.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const logsBox = document.getElementById('modalLogsBox');
  document.getElementById('modalExecutionLogs').classList.remove('hidden');
  logsBox.innerHTML = `<div class="text-indigo-400">Fazendo upload de ${file.name}...</div>`;

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      logsBox.innerHTML += `<div class="text-emerald-400">Upload concluído com sucesso!</div>`;
      await openNewDiarizeModal(); // recarrega a lista com o novo arquivo
      document.getElementById('modalFileInput').value = file.name;
    } else {
      logsBox.innerHTML += `<div class="text-rose-400">Erro no upload do arquivo.</div>`;
    }
  } catch (err) {
    logsBox.innerHTML += `<div class="text-rose-400">Erro de rede: ${err}</div>`;
  }
}

async function startDiarizationJob() {
  const fileName = document.getElementById('modalFileInput').value;
  if (!fileName) {
    alert('Selecione ou faça upload de um arquivo de áudio antes de prosseguir.');
    return;
  }

  const engine = document.getElementById('modalEngine').value;
  const codec = document.getElementById('modalCodec').value;
  const model = document.getElementById('modalModel').value;
  const vad = document.getElementById('modalVad').checked;
  const review = document.getElementById('modalReview').checked;

  const btnStart = document.getElementById('btnStartDiarize');
  btnStart.disabled = true;
  btnStart.classList.add('opacity-50');

  const logsContainer = document.getElementById('modalExecutionLogs');
  const logsBox = document.getElementById('modalLogsBox');
  const progressBar = document.getElementById('modalProgressBar');
  const progressText = document.getElementById('modalProgressText');

  logsContainer.classList.remove('hidden');
  logsBox.innerHTML = '<div class="text-purple-400">Disparando requisição de diarização...</div>';
  progressBar.style.width = '10%';
  progressText.textContent = '10%';

  try {
    const res = await fetch('/api/diarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_name: fileName,
        engine: engine,
        codec: codec,
        model: model,
        vad: vad,
        review: review
      })
    });
    const data = await res.json();
    const taskId = data.task_id;

    // Conecta via Server-Sent Events (SSE)
    const evtSource = new EventSource(`/api/tasks/${taskId}/events`);

    evtSource.addEventListener('log', (e) => {
      const logEntry = JSON.parse(e.data);
      const row = document.createElement('div');
      row.className = logEntry.level === 'ERROR' ? 'text-rose-400' : 'text-slate-300';
      row.textContent = `[${logEntry.time}] ${logEntry.message}`;
      logsBox.appendChild(row);
      logsBox.scrollTop = logsBox.scrollHeight;
    });

    evtSource.addEventListener('status', async (e) => {
      const statusData = JSON.parse(e.data);
      progressBar.style.width = `${statusData.progress}%`;
      progressText.textContent = `${statusData.progress}%`;

      if (statusData.status === 'completed') {
        evtSource.close();
        btnStart.disabled = false;
        btnStart.classList.remove('opacity-50');
        logsBox.innerHTML += '<div class="text-emerald-400 font-bold mt-2">Diarização finalizada com sucesso! Recarregando...</div>';

        await loadReports();
        if (statusData.result?.report_json) {
          document.getElementById('reportSelect').value = statusData.result.report_json;
          await loadSelectedReport();
        }
        setTimeout(() => closeNewDiarizeModal(), 1500);
      } else if (statusData.status === 'error') {
        evtSource.close();
        btnStart.disabled = false;
        btnStart.classList.remove('opacity-50');
        logsBox.innerHTML += `<div class="text-rose-400 font-bold mt-2">Erro: ${statusData.error}</div>`;
      }
    });

  } catch (err) {
    btnStart.disabled = false;
    btnStart.classList.remove('opacity-50');
    logsBox.innerHTML += `<div class="text-rose-400">Falha ao iniciar diarização: ${err}</div>`;
  }
}

// ==========================================
// UTILITÁRIOS
// ==========================================
function formatSeconds(sec) {
  if (isNaN(sec) || sec === null) return '00:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function formatMinutes(sec) {
  if (isNaN(sec) || sec === null) return '--';
  const min = (sec / 60).toFixed(2);
  return `${min} min (${Math.round(sec)}s)`;
}

function escapeJsString(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Espaço para Play/Pause se não estiver digitando em input
    if (e.code === 'Space' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
      e.preventDefault();
      togglePlayPause();
    }
  });
}
