"use strict";

/* Pauta: tela principal "Minhas aulas" (#/). */

import { api } from "../api.js";
import { h, svgIcon, view } from "../dom.js";
import { formatDate, formatDuration } from "../format.js";
import { navigate } from "../router.js";

const STATUS_LABELS = {
  queued: "Na fila",
  processing: "Processando",
  done: "Pronta",
  failed: "Falhou",
};

export function renderSessions({ me, onNavigate }) {
  const v = view();
  let pollTimer = null;
  let loading = true;
  let errorMessage = "";
  let sessions = [];
  let retryingId = null;

  function cleanup() {
    if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  }

  async function loadSessions(silent = false) {
    if (!silent) {
      loading = true;
      render();
    }
    try {
      sessions = await api.sessions();
      errorMessage = "";
    } catch (err) {
      errorMessage = err.message || "Não foi possível carregar as aulas.";
    } finally {
      loading = false;
      render();
    }

    const hasActive = sessions.some((s) => s.status === "queued" || s.status === "processing");
    cleanup();
    if (hasActive) {
      pollTimer = setTimeout(() => loadSessions(true), 3000);
    }
  }

  async function handleRetry(session) {
    if (retryingId) return;
    retryingId = session.id;
    render();
    try {
      await api.retrySession(session.id);
      await loadSessions(true);
    } catch (err) {
      alert(err.message || "Falha ao reenviar aula para processamento.");
    } finally {
      retryingId = null;
      render();
    }
  }

  async function handleDelete(session) {
    const ok = window.confirm("Excluir esta aula e todo o material? Não dá para desfazer.");
    if (!ok) return;

    try {
      await api.deleteSession(session.id);
      sessions = sessions.filter((s) => s.id !== session.id);
      render();
    } catch (err) {
      alert(err.message || "Falha ao excluir a aula.");
    }
  }

  function render() {
    const trashIcon = [
      "M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2",
    ];

    const quotaText = me
      ? `${Math.round(me.used_minutes_month || 0)} de ${me.monthly_audio_minutes} minutos usados este mês`
      : "";

    const head = h(
      "div",
      { class: "page-head", style: { marginBottom: "24px" } },
      h(
        "div",
        {},
        h("h1", {}, "Minhas aulas"),
        quotaText
          ? h("p", { class: "hint", style: { marginTop: "4px", fontWeight: "600" } }, quotaText)
          : null
      ),
      h(
        "a",
        {
          class: "button button-primary",
          href: "#/nova",
          onClick: (e) => {
            e.preventDefault();
            cleanup();
            navigate("/nova");
          },
        },
        "Nova aula"
      )
    );

    let content;
    if (loading && sessions.length === 0) {
      content = h(
        "div",
        { class: "card state" },
        h("div", { class: "spinner", "aria-hidden": "true" }),
        h("p", {}, "Carregando suas aulas...")
      );
    } else if (errorMessage) {
      content = h(
        "div",
        { class: "card state" },
        h("div", { class: "alert" }, errorMessage),
        h(
          "button",
          {
            class: "button button-primary",
            style: { marginTop: "12px" },
            onClick: () => loadSessions(),
          },
          "Tentar novamente"
        )
      );
    } else if (sessions.length === 0) {
      content = h(
        "div",
        { class: "card state", style: { padding: "48px 20px" } },
        h("h2", { style: { fontSize: "20px" } }, "Nenhuma aula ainda. Envie a primeira gravação."),
        h("p", { class: "hint" }, "Suas gravações processadas e materiais individuais aparecerão aqui."),
        h(
          "a",
          {
            class: "button button-primary",
            style: { marginTop: "16px" },
            href: "#/nova",
            onClick: (e) => {
              e.preventDefault();
              cleanup();
              navigate("/nova");
            },
          },
          "Enviar a primeira gravação"
        )
      );
    } else {
      const items = sessions.map((s) => {
        const isReady = s.status === "done";
        const isFailed = s.status === "failed";
        const isActive = s.status === "queued" || s.status === "processing";

        const statusPill = h(
          "span",
          { class: "pill", "data-status": s.status },
          s.status === "processing" ? h("span", { class: "dot", "data-status": "processing", style: { marginRight: "6px" } }) : null,
          STATUS_LABELS[s.status] || s.status
        );

        const lessonBadge = s.has_lesson
          ? h(
              "span",
              {
                class: "pill",
                style: {
                  background: "var(--ok-soft)",
                  color: "var(--ok)",
                  borderColor: "transparent",
                },
              },
              "Material pronto"
            )
          : null;

        const durationStr = s.audio_seconds ? formatDuration(s.audio_seconds) : "";

        return h(
          "li",
          {
            class: "card",
            style: {
              padding: "16px 20px",
              display: "grid",
              gap: "10px",
              marginBottom: "12px",
            },
          },
          h(
            "div",
            {
              style: {
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "8px",
              },
            },
            h(
              "div",
              { style: { display: "flex", alignItems: "center", gap: "10px", minWidth: 0 } },
              h(
                "a",
                {
                  href: `#/aulas/${s.id}`,
                  style: {
                    fontWeight: "700",
                    fontSize: "18px",
                    textDecoration: "none",
                    color: "var(--ink)",
                    overflowWrap: "anywhere",
                  },
                  onClick: (e) => {
                    e.preventDefault();
                    cleanup();
                    navigate(`/aulas/${s.id}`);
                  },
                },
                s.file_name
              ),
              statusPill,
              lessonBadge
            ),
            h(
              "div",
              { style: { display: "flex", alignItems: "center", gap: "8px" } },
              h(
                "a",
                {
                  class: "button button-sm",
                  href: `#/aulas/${s.id}`,
                  onClick: (e) => {
                    e.preventDefault();
                    cleanup();
                    navigate(`/aulas/${s.id}`);
                  },
                },
                "Abrir aula"
              ),
              isFailed
                ? h(
                    "button",
                    {
                      class: "button button-sm button-primary",
                      disabled: retryingId === s.id,
                      onClick: () => handleRetry(s),
                    },
                    retryingId === s.id ? "Reenviando..." : "Tentar novamente"
                  )
                : null,
              s.has_lesson
                ? h(
                    "a",
                    {
                      class: "button button-sm button-primary",
                      href: `#/aulas/${s.id}/atividades`,
                      onClick: (e) => {
                        e.preventDefault();
                        cleanup();
                        navigate(`/aulas/${s.id}/atividades`);
                      },
                    },
                    "Ver atividades"
                  )
                : null,
              h(
                "button",
                {
                  class: "button button-sm button-ghost",
                  title: "Excluir aula",
                  "aria-label": `Excluir aula ${s.file_name}`,
                  onClick: () => handleDelete(s),
                },
                svgIcon(trashIcon, "dropzone-icon")
              )
            )
          ),
          h(
            "div",
            {
              class: "hint",
              style: { display: "flex", gap: "16px", flexWrap: "wrap" },
            },
            h("span", {}, `Enviada em ${formatDate(s.created_at)}`),
            durationStr ? h("span", {}, `Duração: ${durationStr}`) : null,
            s.error ? h("span", { style: { color: "#8d1424" } }, s.error) : null
          )
        );
      });

      content = h("ul", { style: { listStyle: "none", padding: "0", margin: "0" } }, items);
    }

    v.replaceChildren(head, content);
  }

  loadSessions();

  return cleanup;
}
