"use strict";

/* Pauta: tela da aula (#/aulas/<id>). Quem é quem, player e transcrição. */

import { api } from "../api.js";
import { clear, h, view } from "../dom.js";
import { formatDuration, formatTime } from "../format.js";
import { navigate } from "../router.js";

const SPEAKER_COLORS = ["--s0", "--s1", "--s2", "--s3", "--s4", "--s5"];
const VIDEO_EXTENSIONS = [".mp4", ".mkv", ".webm"];

export function renderSession({ id, activeTab = "aula" }) {
  const v = view();

  let session = null;
  let loading = true;
  let errorMessage = "";
  let pollTimer = null;
  let elapsedTimer = null;
  let secondsElapsed = 0;
  let searchQuery = "";
  let savingParticipants = false;

  function cleanup() {
    if (pollTimer) clearTimeout(pollTimer);
    if (elapsedTimer) clearInterval(elapsedTimer);
  }

  async function loadData() {
    try {
      session = await api.session(id);
      errorMessage = "";
      if (session.status === "queued" || session.status === "processing") {
        if (!elapsedTimer) {
          secondsElapsed = session.elapsed_sec || 0;
          elapsedTimer = setInterval(() => {
            secondsElapsed += 1;
            renderTimer();
          }, 1000);
        }
        pollTimer = setTimeout(loadData, 1500);
      } else {
        if (elapsedTimer) clearInterval(elapsedTimer);
      }
    } catch (err) {
      errorMessage = err.message || "Não foi possível carregar os detalhes da aula.";
    } finally {
      loading = false;
      render();
    }
  }

  function renderTimer() {
    const timerEl = document.getElementById("session-timer");
    if (timerEl) {
      timerEl.textContent = formatTime(secondsElapsed);
    }
  }

  async function handleDelete() {
    const ok = window.confirm("Excluir esta aula e todo o material? Não dá para desfazer.");
    if (!ok) return;
    try {
      await api.deleteSession(id);
      cleanup();
      navigate("/");
    } catch (err) {
      alert(err.message || "Falha ao excluir a aula.");
    }
  }

  async function saveParticipants(participantsMap) {
    savingParticipants = true;
    try {
      const payload = Object.entries(participantsMap).map(([label, p]) => ({
        label,
        name: (p.name || label).trim(),
        role: p.role,
      }));
      const updated = await api.updateParticipants(id, payload);
      session.participants = updated.participants || payload;
    } catch (err) {
      console.error("Falha ao salvar participantes:", err);
    } finally {
      savingParticipants = false;
    }
  }

  function render() {
    if (loading && !session) {
      v.replaceChildren(
        h("div", { class: "card state" },
          h("div", { class: "spinner", "aria-hidden": "true" }),
          h("p", {}, "Carregando aula...")
        )
      );
      return;
    }

    if (errorMessage && !session) {
      v.replaceChildren(
        h("div", { class: "card state" },
          h("div", { class: "alert" }, errorMessage),
          h("a", { class: "button button-primary", style: { marginTop: "12px" }, href: "#/" }, "Voltar para Minhas aulas")
        )
      );
      return;
    }

    if (session.status === "queued" || session.status === "processing") {
      v.replaceChildren(
        h("div", { class: "card state", style: { padding: "50px 20px" } },
          h("div", { class: "spinner", "aria-hidden": "true" }),
          h("div", { id: "session-timer", class: "timer" }, formatTime(secondsElapsed)),
          h("h2", { style: { fontSize: "20px" } }, session.status === "queued" ? "Na fila para transcrição" : "Transcrevendo a aula..."),
          h("p", { class: "hint" }, "Você pode sair desta página se quiser. O processamento continua no servidor."),
          h("button", {
            class: "button button-ghost button-sm",
            style: { marginTop: "16px" },
            onClick: handleDelete,
          }, "Cancelar e excluir aula")
        )
      );
      return;
    }

    if (session.status === "failed") {
      v.replaceChildren(
        h("div", { class: "card state" },
          h("h2", {}, "Falha no processamento"),
          h("div", { class: "alert", role: "alert" }, session.error || "Ocorreu um erro ao processar o arquivo de áudio."),
          h("div", { style: { display: "flex", gap: "10px", marginTop: "16px" } },
            h("a", { class: "button button-primary", href: "#/nova" }, "Tentar outro arquivo"),
            h("button", { class: "button button-ghost", onClick: handleDelete }, "Excluir aula")
          )
        )
      );
      return;
    }

    // Aula pronta (done)
    const navTabs = h(
      "div",
      { class: "tabs" },
      h("a", {
        class: "tab",
        "aria-selected": activeTab === "aula" ? "true" : "false",
        href: `#/aulas/${id}`,
        onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}`); },
      }, "Aula"),
      h("a", {
        class: "tab",
        "aria-selected": activeTab === "atividades" ? "true" : "false",
        href: `#/aulas/${id}/atividades`,
        onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}/atividades`); },
      },
        "Atividades",
        session.has_lesson ? h("span", { class: "tab-badge" }, "pronto") : null
      ),
      h("a", {
        class: "tab",
        "aria-selected": activeTab === "proxima" ? "true" : "false",
        href: `#/aulas/${id}/proxima`,
        onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}/proxima`); },
      }, "Próxima aula")
    );

    const head = h(
      "div",
      { class: "page-head" },
      h("div", {},
        h("h1", {}, session.file_name),
        h("p", { class: "hint", style: { marginTop: "4px" } },
          session.audio_seconds ? `Duração: ${formatDuration(session.audio_seconds)}` : ""
        )
      ),
      h("button", {
        class: "button button-sm button-ghost",
        onClick: handleDelete,
      }, "Excluir aula")
    );

    // Player
    const isVideo = VIDEO_EXTENSIONS.some((ext) => session.file_name.toLowerCase().endsWith(ext));
    const mediaEl = isVideo
      ? h("video", { controls: true, preload: "metadata", src: api.mediaUrl(id) })
      : h("audio", { controls: true, preload: "metadata", src: api.mediaUrl(id) });
    const playerWrapper = h("div", { class: "card player" }, mediaEl);

    // Pessoas / Quem é quem
    const result = session.result || {};
    const segments = result.segmentos || [];
    const reviewedNames = result.revisao?.nomes_aplicados || {};
    const speakers = [];
    const speakerDurations = {};
    let totalDuration = 0;
    for (const seg of segments) {
      const spk = seg.quemfala || "Desconhecido";
      if (!speakers.includes(spk)) speakers.push(spk);
      const dur = Math.max(0, (seg.segundos_fim || 0) - (seg.segundos_inicio || 0));
      speakerDurations[spk] = (speakerDurations[spk] || 0) + dur;
      totalDuration += dur;
    }
    totalDuration = totalDuration || 1;

    const partMap = {};
    for (const p of session.participants || []) {
      partMap[p.label] = { name: p.name, role: p.role };
    }
    const topSpeaker = speakers.reduce((best, spk) => (
      !best || (speakerDurations[spk] || 0) > (speakerDurations[best] || 0) ? spk : best
    ), null);
    const hasTeacherHint = (label, name) => /prof|teacher|tutor/i.test(`${label} ${name}`);

    const peopleItems = speakers.map((speaker, idx) => {
      const colorVar = SPEAKER_COLORS[idx % SPEAKER_COLORS.length];
      const suggestedName = reviewedNames[speaker] || speaker;
      const guessedTeacher = speakers.some((s) => hasTeacherHint(s, reviewedNames[s] || ""))
        ? hasTeacherHint(speaker, suggestedName)
        : speaker === topSpeaker;
      const current = partMap[speaker] || {
        name: suggestedName,
        role: guessedTeacher ? "teacher" : "student",
      };
      partMap[speaker] = current;

      const dur = speakerDurations[speaker] || 0;
      const pct = Math.round((dur / totalDuration) * 100);

      const nameInput = h("input", {
        type: "text",
        value: current.name,
        placeholder: speaker,
        onBlur: (e) => {
          const val = e.target.value.trim();
          if (val && val !== current.name) {
            current.name = val;
            saveParticipants(partMap);
          }
        },
      });

      const teacherRadio = h("input", {
        type: "radio",
        name: `role-${speaker}`,
        value: "teacher",
        checked: current.role === "teacher",
        onChange: () => {
          current.role = "teacher";
          saveParticipants(partMap);
          render();
        },
      });

      const studentRadio = h("input", {
        type: "radio",
        name: `role-${speaker}`,
        value: "student",
        checked: current.role === "student",
        onChange: () => {
          current.role = "student";
          saveParticipants(partMap);
          render();
        },
      });

      return h(
        "li",
        { class: "person" },
        h("span", { class: "swatch", style: { background: `var(${colorVar})` } }),
        nameInput,
        h("div", { class: "role-switch" },
          h("label", {}, teacherRadio, "Professor"),
          h("label", {}, studentRadio, "Aluno")
        ),
        h("span", { class: "share" }, `${pct}%`)
      );
    });

    const peopleCard = h(
      "div",
      { class: "card people" },
      h("h3", { style: { fontSize: "18px" } }, "Quem é quem"),
      h("ul", { class: "people-list" }, peopleItems)
    );

    // Toolbar de busca e transcrição
    const searchInput = h("input", {
      type: "search",
      class: "search",
      placeholder: "Buscar palavra na aula...",
      value: searchQuery,
      onInput: (e) => {
        searchQuery = e.target.value;
        updateTranscript();
      },
    });

    const copyBtn = h("button", {
      class: "button button-sm",
      onClick: async () => {
        const text = segments
          .map((s) => `[${formatTime(s.segundos_inicio)}] ${partMap[s.quemfala]?.name || s.quemfala}: ${s.textodefala}`)
          .join("\n\n");
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = "Copiado!";
        setTimeout(() => { copyBtn.textContent = "Copiar texto"; }, 1500);
      },
    }, "Copiar texto");

    const downloadLink = h("a", {
      class: "button button-sm button-ghost",
      href: api.fileUrl(id, "md"),
      download: `${session.file_name}.md`,
    }, "Baixar Markdown");

    const toolbar = h("div", { class: "toolbar" }, searchInput, copyBtn, downloadLink);

    // Lista de transcrição
    const transcriptList = h("ul", { class: "card transcript" });

    function updateTranscript() {
      clear(transcriptList);
      const query = searchQuery.trim().toLowerCase();
      const filtered = query
        ? segments.filter((s) => (s.textodefala || "").toLowerCase().includes(query))
        : segments;

      if (filtered.length === 0) {
        transcriptList.append(h("li", { class: "no-results" }, "Nenhuma fala encontrada com esse termo."));
        return;
      }

      for (const seg of filtered) {
        const label = seg.quemfala || "Desconhecido";
        const idx = speakers.indexOf(label);
        const colorVar = SPEAKER_COLORS[(idx >= 0 ? idx : 0) % SPEAKER_COLORS.length];
        const participant = partMap[label] || { name: label, role: "student" };
        const isTeacher = participant.role === "teacher";
        const text = seg.textodefala || "";

        const timeBtn = h("button", {
          class: "turn-time",
          onClick: () => {
            if (mediaEl) {
              mediaEl.currentTime = seg.segundos_inicio || 0;
              mediaEl.play();
            }
          },
        }, formatTime(seg.segundos_inicio));

        const turnHeader = h("div", {},
          h("span", { class: "turn-speaker", style: { color: `var(${colorVar})` } }, participant.name || label),
          h("span", { class: "turn-role" }, isTeacher ? "(Professor)" : "(Aluno)")
        );

        let turnBody;
        if (query) {
          const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"));
          const spans = parts.map((part) =>
            part.toLowerCase() === query ? h("mark", {}, part) : document.createTextNode(part)
          );
          turnBody = h("div", { class: "turn-text" }, spans);
        } else {
          turnBody = h("div", { class: "turn-text" }, text);
        }

        const turnEl = h("li", { class: `turn ${isTeacher ? "is-teacher" : ""}` },
          timeBtn,
          h("div", { style: { gridColumn: "2" } }, turnHeader, turnBody)
        );

        transcriptList.append(turnEl);
      }
    }

    updateTranscript();

    v.replaceChildren(
      head,
      navTabs,
      h("div", { class: "panel" },
        playerWrapper,
        peopleCard,
        toolbar,
        transcriptList
      )
    );
  }

  loadData();

  return cleanup;
}
