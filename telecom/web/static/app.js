"use strict";

/* Pauta: interface de página única sem build.
   Rotas por hash: #/ (nova aula), #/jobs/<id> (aula), #/jobs/<id>/atividades e #/jobs/<id>/proxima. */

const POLL_JOB_MS = 1500;
const POLL_LIST_MS = 4000;
const SPEAKER_COLOR_COUNT = 6;
const VIDEO_EXTENSIONS = [".mp4", ".mkv", ".webm"];
const STATUS_LABEL = { queued: "Na fila", processing: "Processando", done: "Pronta", failed: "Falhou" };
const TABS = [
  { id: "aula", label: "Aula" },
  { id: "atividades", label: "Atividades" },
  { id: "proxima", label: "Próxima aula" },
];
const LEVEL_LABEL = {
  A1: "Iniciante (A1)", A2: "Básico (A2)", B1: "Intermediário (B1)",
  B2: "Intermediário avançado (B2)", C1: "Avançado (C1)", C2: "Proficiente (C2)",
};
const DEFAULT_LEVEL = "B1";
const ROLE = { teacher: "teacher", student: "student" };
const ROLE_LABEL = { teacher: "Professor", student: "Aluno" };
const WRITE_LINES = { rewrite: 2, short_answer: 2 };
const MAX_FIX_NOTE_CHARS = 28;
const COPIED_FEEDBACK_MS = 1600;

const state = { config: null, jobs: [], timers: [], file: null, current: null };

/* ---------- DOM ---------- */

function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith("on")) el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === "class") el.className = value;
    else if (key === "style") for (const [prop, val] of Object.entries(value)) el.style.setProperty(prop.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`), val);
    else if (key in el && typeof value !== "string") el[key] = value;
    else el.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

function svgIcon(paths) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "dropzone-icon");
  svg.setAttribute("aria-hidden", "true");
  for (const d of paths) {
    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

const view = () => document.getElementById("view");

/* ---------- API ---------- */

const api = {
  async request(path, options = {}) {
    const response = await fetch(path, { headers: { Accept: "application/json", ...options.headers }, ...options });
    if (!response.ok) throw new Error(await errorDetail(response));
    return response.json();
  },
  config: () => api.request("/api/config"),
  jobs: () => api.request("/api/jobs"),
  job: (id) => api.request(`/api/jobs/${encodeURIComponent(id)}`),
  mediaUrl: (id) => `/api/jobs/${encodeURIComponent(id)}/media`,
  fileUrl: (id, kind) => `/api/jobs/${encodeURIComponent(id)}/files/${kind}`,
  createLesson: (id, body) => api.request(`/api/jobs/${encodeURIComponent(id)}/lesson`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }),

  /* XHR em vez de fetch: só ele informa o progresso do upload. */
  createJob(form, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/jobs");
      xhr.responseType = "json";
      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) onProgress(event.loaded / event.total);
      });
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response);
        else reject(new Error(detailText(xhr.response) || `Erro ${xhr.status}`));
      });
      xhr.addEventListener("error", () => reject(new Error("Sem conexão com o servidor. Confira se ele está rodando.")));
      xhr.send(form);
    });
  },
};

async function errorDetail(response) {
  try {
    return detailText(await response.json()) || `Erro ${response.status}`;
  } catch {
    return `Erro ${response.status}`;
  }
}

function detailText(body) {
  if (!body || !body.detail) return "";
  return typeof body.detail === "string" ? body.detail : body.detail.map((item) => item.msg).join("; ");
}

/* ---------- Armazenamento local (nomes e papéis escolhidos pelo professor) ---------- */

const storage = {
  read(key) {
    try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
  },
  write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* navegação privada: segue sem salvar */ }
  },
};

/* ---------- Formatação ---------- */

function fmtClock(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = String(total % 60).padStart(2, "0");
  return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${secs}` : `${String(minutes).padStart(2, "0")}:${secs}`;
}

function fmtDuration(seconds) {
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours) return `${hours} h ${minutes} min`;
  return minutes ? `${minutes} min` : `${total} s`;
}

const fmtDate = (iso) => new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
const fmtLongDate = (iso) => new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "long", year: "numeric" }).format(new Date(iso));
const fmtSize = (bytes) => (bytes >= 1e6 ? `${(bytes / 1e6).toFixed(1)} MB` : `${Math.ceil(bytes / 1e3)} KB`);
const normalize = (text) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const extensionOf = (name) => (name.match(/\.[^.]+$/) || [""])[0].toLowerCase();

/* "SPEAKER_00" vira "Falante 1"; rótulos legíveis ("Professor", "Aluno 1") ficam como estão. */
function defaultName(label, identified) {
  if (identified) return identified;
  const match = /^SPEAKER_(\d+)$/.exec(label);
  return match ? `Falante ${Number(match[1]) + 1}` : label;
}

/* ---------- Histórico ---------- */

async function refreshJobs() {
  try {
    state.jobs = await api.jobs();
  } catch {
    return;
  }
  renderJobList();
}

function renderJobList() {
  const list = document.getElementById("job-list");
  const activeId = currentRoute().id;
  if (!state.jobs.length) {
    list.replaceChildren(h("li", { class: "empty-note" }, "Nenhuma aula ainda. Envie a primeira gravação."));
    return;
  }
  list.replaceChildren(...state.jobs.map((job) => h("li", {},
    h("a", { class: "job-link", href: `#/jobs/${job.id}`, "aria-current": job.id === activeId ? "page" : null },
      h("span", { class: "dot", "data-status": job.status, title: STATUS_LABEL[job.status] }),
      h("span", { class: "job-name" }, job.file_name),
      h("span", { class: "job-meta" }, `${STATUS_LABEL[job.status]}, ${fmtDate(job.created_at)}`),
    ),
  )));
}

function scheduleListPolling() {
  every(POLL_LIST_MS, () => {
    if (state.jobs.some((job) => job.status === "queued" || job.status === "processing")) refreshJobs();
  });
}

/* ---------- Rotas ---------- */

function currentRoute() {
  const match = /^#\/jobs\/([\w-]+)(?:\/(\w+))?/.exec(location.hash);
  const tab = match && TABS.some((item) => item.id === match[2]) ? match[2] : "aula";
  return { id: match ? match[1] : null, tab };
}

function every(ms, fn) {
  state.timers.push(setInterval(fn, ms));
}

function clearTimers() {
  state.timers.forEach(clearInterval);
  state.timers = [];
}

function route() {
  const { id, tab } = currentRoute();
  /* Trocar de aba não recarrega a aula: o áudio continua tocando. */
  if (id && state.current?.job.id === id) {
    state.current.show(tab);
    renderJobList();
    return;
  }
  clearTimers();
  scheduleListPolling();
  renderJobList();
  state.current = null;
  if (id) renderJob(id, tab);
  else renderUpload();
  view().focus({ preventScroll: true });
}

/* ---------- Nova aula ---------- */

function renderUpload() {
  state.file = null;
  const { engines, review_available: reviewAvailable, extensions } = state.config;
  const firstAvailable = engines.find((engine) => engine.available);

  const error = h("div", { class: "alert", role: "alert", hidden: true });
  const progressBar = h("span", { style: { width: "0%" } });
  const progress = h("div", { class: "progress", hidden: true }, progressBar);
  const submit = h("button", { class: "button button-primary button-block", type: "submit", disabled: true }, "Transcrever a aula");
  const fileSlot = h("div");
  const input = h("input", { type: "file", name: "file", accept: extensions.join(","), onChange: () => setFile(input.files[0]) });

  const dropzone = h("label", { class: "dropzone" },
    input,
    svgIcon(["M12 16V4", "M7 9l5-5 5 5", "M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"]),
    h("span", { class: "dropzone-title" }, "Arraste a gravação aqui ou ", h("u", {}, "escolha no computador")),
    h("span", { class: "hint" }, `Áudio ou vídeo: ${extensions.map((ext) => ext.slice(1)).join(", ")}`),
  );

  function setFile(file) {
    error.hidden = true;
    if (file && !extensions.includes(extensionOf(file.name))) {
      showError(`Formato não suportado: ${file.name}. Use ${extensions.map((ext) => ext.slice(1)).join(", ")}.`);
      file = null;
    }
    state.file = file || null;
    dropzone.hidden = Boolean(state.file);
    fileSlot.replaceChildren(state.file ? h("div", { class: "file-chip" },
      h("div", {}, h("strong", {}, state.file.name), h("div", { class: "hint" }, fmtSize(state.file.size))),
      h("button", { class: "button button-sm", type: "button", onClick: () => { input.value = ""; setFile(null); } }, "Trocar arquivo"),
    ) : "");
    submit.disabled = !state.file || !firstAvailable;
  }

  function showError(message) {
    error.textContent = message;
    error.hidden = false;
  }

  dropzone.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("is-over"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-over"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-over");
    setFile(event.dataTransfer.files[0]);
  });

  const engineChoices = engines.map((engine) => h("label", { class: "choice", title: engine.unavailable_reason || "" },
    h("input", { type: "radio", name: "engine", value: engine.id, checked: engine === firstAvailable, disabled: !engine.available }),
    h("span", { class: "choice-title" }, engine.label),
    h("span", { class: "choice-desc" }, engine.available ? engine.description : engine.unavailable_reason),
  ));

  const toggle = (name, title, description, disabled, checked = false) => h("label", { class: "toggle" },
    h("span", { class: "toggle-text" },
      h("span", { class: "toggle-title" }, title),
      h("span", { class: "hint" }, description),
    ),
    h("input", { type: "checkbox", name, role: "switch", disabled, checked: checked && !disabled }),
  );

  const form = h("form", { class: "card upload", onSubmit: onSubmit },
    h("div", {},
      h("h1", { class: "page-title" }, "Envie a gravação da aula"),
      h("p", { class: "lead" },
        "Separamos quem falou cada trecho. Depois você diz quem é o professor, e a Pauta cria atividades para cada aluno e um plano para a próxima aula."),
    ),
    h("div", {}, dropzone, fileSlot),
    toggle("review", "Descobrir o nome dos alunos", reviewAvailable
      ? "Quando alguém diz o próprio nome ou é chamado pelo nome, a IA usa esse nome na transcrição."
      : "Requer o Gemini configurado.", !reviewAvailable, true),
    h("details", { class: "more" },
      h("summary", {}, "Opções avançadas"),
      h("div", { style: { display: "grid", gap: "20px" } },
        h("fieldset", {}, h("legend", {}, "Como transcrever"), h("div", { class: "choices" }, engineChoices)),
        toggle("compact_silence", "Remover pausas longas",
          "Útil para gravações longas: envia menos áudio e reduz o custo. Os tempos continuam os da gravação original.", false),
      ),
    ),
    !firstAvailable ? h("div", { class: "alert" }, "Nenhum motor de transcrição está configurado. Veja o README.") : null,
    error,
    h("div", { style: { display: "grid", gap: "10px" } }, progress, submit),
  );

  async function onSubmit(event) {
    event.preventDefault();
    if (!state.file) return;
    const data = new FormData();
    data.append("file", state.file);
    data.append("engine", form.elements.engine.value);
    data.append("compact_silence", String(form.elements.compact_silence.checked));
    data.append("review", String(form.elements.review.checked));

    submit.disabled = true;
    submit.textContent = "Enviando…";
    progress.hidden = false;
    error.hidden = true;
    try {
      const job = await api.createJob(data, (ratio) => { progressBar.style.width = `${Math.round(ratio * 100)}%`; });
      await refreshJobs();
      location.hash = `#/jobs/${job.id}`;
    } catch (err) {
      showError(err.message);
      submit.disabled = false;
      submit.textContent = "Transcrever a aula";
      progress.hidden = true;
    }
  }

  view().replaceChildren(form);
}

/* ---------- Aula: estados ---------- */

async function renderJob(id, tab) {
  let job;
  try {
    job = await api.job(id);
  } catch (err) {
    renderMissing(err.message);
    return;
  }
  if (currentRoute().id !== id) return;

  if (job.status === "done") renderResult(job, tab);
  else if (job.status === "failed") renderFailure(job);
  else renderProcessing(job);
}

function jobHeader(job, note) {
  return h("div", { class: "page-head" },
    h("div", {},
      h("h1", {}, job.file_name),
      h("p", { class: "lead" }, note || fmtDate(job.created_at)),
    ),
    h("span", { class: "pill", "data-status": job.status }, STATUS_LABEL[job.status]),
  );
}

function renderMissing(message) {
  view().replaceChildren(h("div", { class: "card state" },
    h("h2", {}, "Aula não encontrada"),
    h("p", {}, `${message} A lista de aulas fica na memória do servidor e some quando ele reinicia.`),
    h("a", { class: "button", href: "#/" }, "Enviar uma gravação"),
  ));
}

function renderFailure(job) {
  view().replaceChildren(jobHeader(job), h("div", { class: "card state" },
    h("h2", {}, "Não foi possível transcrever esta aula"),
    h("div", { class: "alert", role: "alert" }, job.error || "Erro desconhecido."),
    h("a", { class: "button", href: "#/" }, "Tentar com outro arquivo"),
  ));
}

function renderProcessing(job) {
  const startedAt = Date.now() - (job.elapsed_sec || 0) * 1000;
  const timer = h("div", { class: "timer", "aria-live": "off" }, fmtClock(job.elapsed_sec || 0));

  view().replaceChildren(jobHeader(job), h("div", { class: "card state", "aria-busy": "true" },
    h("div", { class: "spinner", role: "status", "aria-label": "Processando" }),
    h("h2", {}, job.status === "queued" ? "A aula está na fila" : "Transcrevendo a aula"),
    timer,
    h("p", {}, "Aulas de uma hora levam alguns minutos. Pode abrir outra página: o processamento continua no servidor."),
  ));

  every(1000, () => { timer.textContent = fmtClock((Date.now() - startedAt) / 1000); });
  every(POLL_JOB_MS, async () => {
    const latest = await api.job(job.id).catch(() => null);
    if (!latest || currentRoute().id !== job.id) return;
    if (latest.status !== job.status) {
      route();
      refreshJobs();
    }
  });
}

/* ---------- Participantes: quem é o professor, quem são os alunos ---------- */

function talkSeconds(segments) {
  const seconds = new Map();
  for (const segment of segments) {
    seconds.set(segment.quemfala, (seconds.get(segment.quemfala) || 0) + Math.max(0, segment.segundos_fim - segment.segundos_inicio));
  }
  return seconds;
}

/* Sugestão inicial: quem tem "prof"/"teacher" no nome, ou quem mais fala. O professor confirma na tela. */
function guessPeople(segments) {
  const seconds = talkSeconds(segments);
  const identified = new Map();
  for (const segment of segments) if (segment.falante_identificado) identified.set(segment.quemfala, segment.falante_identificado);
  const labels = [...seconds.keys()];
  const named = labels.find((label) => /prof|teacher|tutor/i.test(identified.get(label) || label));
  const teacher = named || [...labels].sort((a, b) => seconds.get(b) - seconds.get(a))[0];
  return Object.fromEntries(labels.map((label) => [label, {
    name: defaultName(label, identified.get(label)),
    role: label === teacher ? ROLE.teacher : ROLE.student,
  }]));
}

function loadPeople(job) {
  const guessed = guessPeople(job.result.segmentos);
  const saved = storage.read(`pauta:people:${job.id}`) || {};
  for (const label of Object.keys(guessed)) if (saved[label]) guessed[label] = { ...guessed[label], ...saved[label] };
  return guessed;
}

function speakerColors(segments) {
  const colors = new Map();
  for (const segment of segments) {
    if (!colors.has(segment.quemfala)) colors.set(segment.quemfala, `var(--s${colors.size % SPEAKER_COLOR_COUNT})`);
  }
  return colors;
}

/* ---------- Aula: resultado ---------- */

function renderResult(job, initialTab) {
  const result = job.result;
  const segments = result.segmentos;
  const colors = speakerColors(segments);
  const ctx = {
    job,
    colors,
    people: loadPeople(job),
    tab: initialTab,
    media: null,
    panel: h("div", { class: "panel", role: "tabpanel", tabindex: "-1" }),
    tabButtons: new Map(),
  };
  state.current = ctx;

  const isVideo = VIDEO_EXTENSIONS.includes(extensionOf(job.file_name));
  ctx.media = h(isVideo ? "video" : "audio", { controls: true, preload: "metadata", src: api.mediaUrl(job.id) });

  const tabList = h("div", { class: "tabs", role: "tablist", "aria-label": "Seções da aula" },
    TABS.map((item) => {
      const button = h("button", {
        class: "tab", role: "tab", id: `tab-${item.id}`, type: "button", "aria-controls": "panel",
        onClick: () => { location.hash = item.id === "aula" ? `#/jobs/${job.id}` : `#/jobs/${job.id}/${item.id}`; },
        onKeydown: (event) => moveTab(event, item.id),
      }, item.label);
      ctx.tabButtons.set(item.id, button);
      return button;
    }),
  );
  ctx.panel.id = "panel";

  function moveTab(event, current) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = TABS[(TABS.findIndex((item) => item.id === current) + step + TABS.length) % TABS.length];
    event.preventDefault();
    ctx.tabButtons.get(next.id).focus();
    ctx.tabButtons.get(next.id).click();
  }

  ctx.show = (tab) => {
    ctx.tab = tab;
    for (const [id, button] of ctx.tabButtons) {
      button.setAttribute("aria-selected", String(id === tab));
      button.tabIndex = id === tab ? 0 : -1;
    }
    ctx.panel.setAttribute("aria-labelledby", `tab-${tab}`);
    const badge = ctx.job.lesson ? h("span", { class: "tab-badge" }, "pronto") : null;
    const activities = ctx.tabButtons.get("atividades");
    activities.replaceChildren(...["Atividades", badge].filter(Boolean));
    ctx.panel.replaceChildren(...{ aula: lessonPanel, atividades: activitiesPanel, proxima: planPanel }[tab](ctx).filter(Boolean));
  };

  const speakers = new Set(segments.map((segment) => segment.quemfala)).size;
  view().replaceChildren(
    jobHeader(job, `${fmtLongDate(job.created_at)}, ${fmtDuration(result.duracao_original_segundos)}, ${speakers} ${speakers === 1 ? "voz" : "vozes"}`),
    h("div", { class: "card player" }, ctx.media),
    tabList,
    ctx.panel,
  );
  ctx.show(initialTab);
}

const displayName = (ctx, label) => ctx.people[label]?.name || defaultName(label);
const isStudent = (ctx, label) => ctx.people[label]?.role === ROLE.student;

/* Aba "Aula": quem é quem e a transcrição, com os erros marcados a caneta vermelha quando há material. */
function lessonPanel(ctx) {
  const { job } = ctx;
  const segments = job.result.segmentos;
  const mistakes = mistakesBySpeaker(job.lesson);
  const reviews = groupSuggestions(job.result.revisao?.revisoes || []);

  const items = segments.map((segment, index) => {
    const text = h("p", { class: "turn-text" });
    const role = h("span", { class: "turn-role" });
    const name = h("span", { class: "turn-speaker" }, "", role);
    const item = h("li", { class: "turn", style: { "--speaker": ctx.colors.get(segment.quemfala) } },
      h("button", { class: "turn-time", type: "button", title: "Ouvir a partir daqui",
        onClick: () => { ctx.media.currentTime = segment.segundos_inicio; ctx.media.play(); } },
        fmtClock(segment.segundos_inicio)),
      name,
      text,
    );
    return { segment, item, text, name, role, reviews: reviews.get(index) || [] };
  });

  const transcript = h("ol", { class: "transcript card" });
  const search = h("input", { class: "search", type: "search", placeholder: "Buscar na transcrição", "aria-label": "Buscar na transcrição",
    onInput: () => renderTurns(search.value.trim()) });

  function renderTurns(query) {
    const needle = normalize(query);
    const visible = items.filter(({ segment }) => !needle || normalize(segment.textodefala).includes(needle));
    for (const entry of items) {
      const label = entry.segment.quemfala;
      entry.name.firstChild.textContent = displayName(ctx, label);
      const name = displayName(ctx, label);
      /* Só acrescenta "Professor" quando o nome não diz isso por si. */
      entry.role.textContent = isStudent(ctx, label) || name === ROLE_LABEL.teacher ? "" : ROLE_LABEL.teacher;
      entry.item.classList.toggle("is-teacher", !isStudent(ctx, label));
    }
    for (const entry of visible) {
      const label = entry.segment.quemfala;
      const notes = isStudent(ctx, label) ? [...(mistakes.get(label) || []).map(fixNote)] : [];
      entry.text.replaceChildren(...(query
        ? highlightMatches(entry.segment.textodefala, query)
        : markup(entry.segment.textodefala, [...notes, ...entry.reviews.map(reviewNote)])));
    }
    transcript.replaceChildren(...(visible.length
      ? visible.map((entry) => entry.item)
      : [h("li", { class: "no-results" }, `Nenhuma fala com “${query}”.`)]));
  }

  /* Destaca a fala que está tocando. */
  let current = null;
  ctx.media.addEventListener("timeupdate", () => {
    const t = ctx.media.currentTime;
    const entry = items.find(({ segment }) => t >= segment.segundos_inicio && t < segment.segundos_fim);
    if (entry?.item === current) return;
    current?.classList.remove("is-current");
    current = entry?.item || null;
    current?.classList.add("is-current");
  });

  const copyButton = h("button", { class: "button button-sm", type: "button", onClick: async () => {
    const text = segments.map((s) => `[${fmtClock(s.segundos_inicio)}] ${displayName(ctx, s.quemfala)}: ${s.textodefala}`).join("\n");
    await navigator.clipboard.writeText(text);
    copyButton.textContent = "Copiado";
    setTimeout(() => { copyButton.textContent = "Copiar texto"; }, COPIED_FEEDBACK_MS);
  } }, "Copiar texto");

  const hasMarks = mistakes.size > 0;
  const hasReviews = reviews.size > 0;
  const notice = hasMarks
    ? "Os erros em vermelho vieram da IA e estão escritos acima de cada trecho. Passe o mouse para ver a explicação."
    : hasReviews ? "Trechos com pontilhado são sugestões da revisão por IA. Passe o mouse para ver." : null;

  renderTurns("");
  return [
    peoplePanel(ctx, () => renderTurns(search.value.trim())),
    h("div", { class: "toolbar" },
      search,
      copyButton,
      h("a", { class: "button button-sm", href: api.fileUrl(job.id, "md"), download: "" }, "Baixar texto"),
    ),
    notice ? h("p", { class: "hint" }, notice) : null,
    transcript,
  ];
}

function peoplePanel(ctx, onChange) {
  const seconds = talkSeconds(ctx.job.result.segmentos);
  const total = [...seconds.values()].reduce((a, b) => a + b, 0) || 1;

  const rows = [...ctx.colors.keys()].map((label) => {
    const name = h("input", { type: "text", value: ctx.people[label].name, "aria-label": `Nome de ${label}`,
      onInput: () => update(label, { name: name.value.trim() || defaultName(label) }) });
    const radio = (role) => h("label", {},
      h("input", { type: "radio", name: `role-${label}`, value: role, checked: ctx.people[label].role === role,
        onChange: () => update(label, { role }) }),
      ROLE_LABEL[role]);
    return h("li", { class: "person", style: { "--speaker": ctx.colors.get(label) } },
      h("span", { class: "swatch" }),
      name,
      h("span", { class: "role-switch", role: "group", "aria-label": `Papel de ${ctx.people[label].name}` }, radio(ROLE.teacher), radio(ROLE.student)),
      h("span", { class: "share" }, `${Math.round((seconds.get(label) / total) * 100)}% da fala`),
    );
  });

  function update(label, changes) {
    ctx.people[label] = { ...ctx.people[label], ...changes };
    storage.write(`pauta:people:${ctx.job.id}`, ctx.people);
    onChange();
  }

  return h("section", { class: "card people", "aria-labelledby": "people-title" },
    h("div", {},
      h("h2", { id: "people-title", class: "panel-title" }, "Quem é quem nesta aula"),
      h("p", { class: "hint" }, "Confirme o professor e corrija os nomes. Só os alunos recebem folha de atividades."),
    ),
    h("ul", { class: "people-list" }, rows),
  );
}

/* ---------- Marcações no texto ---------- */

function mistakesBySpeaker(lesson) {
  const map = new Map();
  for (const sheet of lesson?.students || []) map.set(sheet.speaker, sheet.mistakes);
  return map;
}

const fixNote = (mistake) => ({
  find: mistake.quote,
  render: (text) => h("ruby", { class: "fix", title: `${mistake.correction}\n${mistake.explanation}`, tabindex: 0 },
    text, h("rt", {}, shortNote(mistake.correction))),
});

const reviewNote = (review) => ({
  find: review.trecho,
  render: (text) => h("span", { class: "suggestion", title: `Sugestão: ${review.sugestao}\n${review.motivo}` }, text),
});

const shortNote = (text) => (text.length > MAX_FIX_NOTE_CHARS ? `${text.slice(0, MAX_FIX_NOTE_CHARS - 1)}…` : text);

/* Aplica as marcações sem sobrepor: a primeira que encontrar o trecho vence. */
function markup(text, notes) {
  const lower = text.toLowerCase();
  const ranges = notes
    .map((note) => ({ ...note, start: lower.indexOf(note.find.toLowerCase()) }))
    .filter((note) => note.start >= 0)
    .sort((a, b) => a.start - b.start);
  const parts = [];
  let cursor = 0;
  for (const note of ranges) {
    if (note.start < cursor) continue;
    parts.push(text.slice(cursor, note.start), note.render(text.slice(note.start, note.start + note.find.length)));
    cursor = note.start + note.find.length;
  }
  parts.push(text.slice(cursor));
  return parts;
}

function groupSuggestions(reviews) {
  const byTurn = new Map();
  for (const review of reviews) {
    if (!byTurn.has(review.indice_fala)) byTurn.set(review.indice_fala, []);
    byTurn.get(review.indice_fala).push(review);
  }
  return byTurn;
}

function highlightMatches(text, query) {
  const lower = text.toLowerCase();
  const needle = query.toLowerCase();
  const parts = [];
  let cursor = 0;
  let index = lower.indexOf(needle);
  while (needle && index >= 0) {
    parts.push(text.slice(cursor, index), h("mark", {}, text.slice(index, index + needle.length)));
    cursor = index + needle.length;
    index = lower.indexOf(needle, cursor);
  }
  parts.push(text.slice(cursor));
  return parts;
}

/* ---------- Aba "Atividades" ---------- */

function activitiesPanel(ctx) {
  return ctx.job.lesson && !ctx.regenerate ? sheetsView(ctx) : [lessonMaker(ctx)];
}

function lessonMaker(ctx) {
  const config = state.config;
  const students = Object.values(ctx.people).filter((person) => person.role === ROLE.student);
  const error = h("div", { class: "alert", role: "alert", hidden: true });
  const submit = h("button", { class: "button button-primary button-block", type: "submit" }, "Criar atividades e plano");

  const level = h("select", { id: "level", name: "level" },
    config.levels.map((id) => h("option", { value: id, selected: id === DEFAULT_LEVEL }, LEVEL_LABEL[id] || id)));
  const count = h("input", { id: "count", name: "count", type: "number", inputmode: "numeric",
    min: config.min_exercises, max: config.max_exercises, value: config.default_exercises });
  const focus = h("textarea", { id: "focus", name: "focus", maxLength: config.max_focus_chars,
    placeholder: "Ex.: passado simples, vocabulário de viagem, perguntas com “do” e “does”",
    onInput: () => { counter.textContent = `${focus.value.length}/${config.max_focus_chars}`; } });
  const counter = h("span", { class: "hint counter" }, `0/${config.max_focus_chars}`);

  const blocked = !config.lessons_available
    ? "Criar atividades usa o Gemini, que não está configurado. Veja o README."
    : !students.length ? "Marque pelo menos um participante como aluno na aba Aula." : null;
  submit.disabled = Boolean(blocked);

  async function onSubmit(event) {
    event.preventDefault();
    submit.disabled = true;
    submit.textContent = "Criando o material…";
    error.hidden = true;
    const body = {
      level: level.value,
      exercises_per_student: Number(count.value),
      focus: focus.value,
      participants: Object.entries(ctx.people).map(([label, person]) => ({ label, name: person.name, role: person.role })),
    };
    try {
      const updated = await api.createLesson(ctx.job.id, body);
      ctx.job.lesson = updated.lesson;
      ctx.regenerate = false;
      location.hash = `#/jobs/${ctx.job.id}/atividades`;
      ctx.show("atividades");
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
      submit.disabled = Boolean(blocked);
      submit.textContent = "Criar atividades e plano";
    }
  }

  return h("form", { class: "card maker", onSubmit },
    h("div", {},
      h("h2", { class: "panel-title" }, "Atividades para cada aluno"),
      h("p", { class: "lead" },
        `A IA lê o que ${students.length === 1 ? "o aluno disse" : `os ${students.length} alunos disseram`} e cria atividades para os erros de cada um, `
        + "mais um plano para a próxima aula."),
    ),
    h("div", { class: "field" }, h("label", { for: "level" }, "Nível da turma"), level),
    h("div", { class: "field" },
      h("label", { for: "count" }, "Atividades por aluno"), count,
      h("span", { class: "hint" }, `De ${config.min_exercises} a ${config.max_exercises}.`)),
    h("div", { class: "field" },
      h("label", { for: "focus" }, "Foco da próxima aula (opcional)"), focus, counter),
    h("p", { class: "notice" },
      "A IA lê só o texto da transcrição, sem ouvir o áudio. Uma palavra mal transcrita pode virar “erro” do aluno. "
      + "Confira o material antes de entregar."),
    blocked ? h("div", { class: "alert" }, blocked) : null,
    error,
    h("div", { class: "maker-actions" }, submit),
  );
}

function sheetsView(ctx) {
  const { job } = ctx;
  const sheets = job.lesson.students;
  const date = fmtLongDate(job.created_at);

  const actions = h("div", { class: "sheet-actions" },
    h("p", { class: "hint" }, "Confira o material antes de entregar. A IA não ouviu o áudio."),
    h("div", { class: "toolbar" },
      h("button", { class: "button button-primary button-sm", type: "button",
        onClick: () => printDocuments(`Atividades, ${date}`, sheets.map((sheet) => sheetDocument(ctx, sheet, { answers: false }))) },
        "Imprimir todas as folhas"),
      h("button", { class: "button button-sm", type: "button",
        onClick: () => printDocuments(`Gabarito, ${date}`, [answerKeyDocument(ctx)]) }, "Imprimir gabarito"),
      h("button", { class: "button button-sm", type: "button",
        onClick: () => { ctx.regenerate = true; ctx.show("atividades"); } }, "Criar de novo"),
    ),
  );

  return [
    actions,
    h("div", { class: "sheets" }, sheets.map((sheet) => h("article", { "aria-label": `Folha de ${displayName(ctx, sheet.speaker)}` },
      sheetDocument(ctx, sheet, { answers: true }),
      h("div", { class: "toolbar", style: { marginTop: "10px" } },
        h("button", { class: "button button-sm", type: "button",
          onClick: () => printDocuments(`Atividades, ${displayName(ctx, sheet.speaker)}, ${date}`, [sheetDocument(ctx, sheet, { answers: false })]) },
          `Imprimir folha de ${displayName(ctx, sheet.speaker)}`),
      ),
    ))),
  ];
}

/* A folha. Com answers, mostra o gabarito (tela do professor); sem, é a folha que vai ao aluno. */
function sheetDocument(ctx, sheet, { answers }) {
  const name = displayName(ctx, sheet.speaker);
  return h("section", { class: "paper" },
    h("div", { class: "paper-head" },
      h("h3", {}, name),
      h("span", { class: "hint" }, fmtLongDate(ctx.job.created_at)),
    ),
    answers && sheet.strength ? h("p", { class: "strength" }, sheet.strength) : null,
    sheet.mistakes.length ? [
      h("h4", {}, "Para revisar"),
      h("ul", { class: "review-list" }, sheet.mistakes.map((mistake) => h("li", { class: "review-item" },
        h("span", {}, h("del", {}, mistake.quote), " → ", h("ins", {}, mistake.correction)),
        h("span", { class: "why" }, mistake.explanation)))),
    ] : null,
    h("h4", {}, "Atividades"),
    sheet.exercises.length
      ? h("ol", { class: "exercises" }, sheet.exercises.map((exercise) => exerciseItem(exercise, answers)))
      : h("p", { class: "empty-sheet" }, "Sem atividades para este aluno."),
  );
}

function exerciseItem(exercise, answers) {
  return h("li", {},
    h("p", { class: "ex-prompt" }, exercise.prompt),
    exercise.options.length ? h("ol", { class: "ex-options" }, exercise.options.map((option) => h("li", {}, option))) : null,
    Array.from({ length: WRITE_LINES[exercise.kind] || 0 }, () => h("span", { class: "write-line" })),
    answers ? h("p", { class: "answer" }, h("span", {}, "Resposta"), exercise.answer) : null,
  );
}

function answerKeyDocument(ctx) {
  return h("section", { class: "paper" },
    h("div", { class: "paper-head" }, h("h3", {}, "Gabarito"), h("span", { class: "hint" }, fmtLongDate(ctx.job.created_at))),
    ctx.job.lesson.students.map((sheet) => [
      h("h4", {}, displayName(ctx, sheet.speaker)),
      h("ol", { class: "exercises" }, sheet.exercises.map((exercise) => h("li", {},
        h("p", { class: "ex-prompt" }, exercise.prompt),
        h("p", { class: "answer" }, h("span", {}, "Resposta"), exercise.answer)))),
    ]),
  );
}

/* ---------- Aba "Próxima aula" ---------- */

function planPanel(ctx) {
  const { lesson } = ctx.job;
  if (!lesson) {
    return [h("div", { class: "card state" },
      h("h2", {}, "O plano nasce junto com as atividades"),
      h("p", {}, "Crie as atividades dos alunos e a Pauta propõe a próxima aula com base no que aconteceu nesta."),
      h("a", { class: "button button-primary", href: `#/jobs/${ctx.job.id}/atividades` }, "Criar atividades e plano"),
    )];
  }
  const date = fmtLongDate(ctx.job.created_at);
  return [
    h("div", { class: "sheet-actions" },
      h("p", { class: "hint" }, "Sugestão da IA a partir desta aula. Ajuste ao seu ritmo."),
      h("button", { class: "button button-primary button-sm", type: "button",
        onClick: () => printDocuments(`Plano da próxima aula, ${date}`, [planDocument(lesson.plan)]) }, "Imprimir plano"),
    ),
    planDocument(lesson.plan),
  ];
}

function planDocument(plan) {
  const total = plan.blocks.reduce((sum, block) => sum + block.minutes, 0);
  return h("section", { class: "paper" },
    h("div", { class: "paper-head" },
      h("h3", {}, "Plano da próxima aula"),
      total ? h("span", { class: "hint" }, `${total} minutos`) : null,
    ),
    h("p", {}, plan.objective),
    plan.topics.length ? [h("h4", {}, "Retomar"), h("ul", { class: "topic-list" }, plan.topics.map((topic) => h("li", {}, topic)))] : null,
    plan.blocks.length ? [
      h("h4", {}, "Etapas"),
      h("ol", { class: "plan-blocks" }, plan.blocks.map((block) => h("li", { class: "plan-block" },
        h("div", { class: "plan-min" }, block.minutes, h("small", {}, "min")),
        h("div", {}, h("h4", {}, block.title), h("p", {}, block.description))))),
    ] : null,
    plan.homework ? [h("h4", {}, "Tarefa de casa"), h("p", {}, plan.homework)] : null,
  );
}

/* ---------- Impressão ---------- */

/* Copia só o que vai ao papel para #print-root; o CSS esconde o resto. O título vira o nome sugerido do PDF. */
function printDocuments(title, nodes) {
  const root = document.getElementById("print-root");
  const previousTitle = document.title;
  root.replaceChildren(...nodes);
  document.title = title;
  document.body.classList.add("printing");
  window.addEventListener("afterprint", () => {
    document.body.classList.remove("printing");
    document.title = previousTitle;
    root.replaceChildren();
  }, { once: true });
  window.print();
}

/* ---------- Início ---------- */

async function start() {
  try {
    state.config = await api.config();
  } catch (err) {
    view().replaceChildren(h("div", { class: "card state" }, h("h2", {}, "Servidor indisponível"), h("p", {}, err.message)));
    return;
  }
  await refreshJobs();
  window.addEventListener("hashchange", route);
  route();
}

start();
