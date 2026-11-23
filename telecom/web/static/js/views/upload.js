"use strict";

/* Pauta: tela de envio de gravação (#/nova). */

import { api } from "../api.js";
import { h, svgIcon, view } from "../dom.js";
import { formatBytes } from "../format.js";
import { navigate } from "../router.js";

const MAX_UPLOAD_BYTES = 300 * 1024 * 1024; // 300 MB
const DEFAULT_EXTENSIONS = [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mkv", ".webm"];

export function renderUpload({ config }) {
  const v = view();

  let file = null;
  let consentGiven = false;
  let compactSilence = false;
  let review = false;
  let selectedEngine = "gemini";
  let uploading = false;
  let progress = 0;
  let errorMessage = "";

  const allowedExts = config?.extensions || DEFAULT_EXTENSIONS;

  function validateFile(candidate) {
    if (!candidate) return null;
    const name = candidate.name.toLowerCase();
    const hasValidExt = allowedExts.some((ext) => name.endsWith(ext));
    if (!hasValidExt) {
      return `Formato de arquivo não suportado: ${candidate.name}. Use formatos aceitos (${allowedExts.join(", ")}).`;
    }
    if (candidate.size > MAX_UPLOAD_BYTES) {
      return `O arquivo tem ${formatBytes(candidate.size)} e excede o limite máximo permitido de 300 MB.`;
    }
    return null;
  }

  function handleFileSelection(newFile) {
    errorMessage = "";
    const error = validateFile(newFile);
    if (error) {
      errorMessage = error;
      file = null;
    } else {
      file = newFile;
    }
    render();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file || !consentGiven || uploading) return;

    uploading = true;
    errorMessage = "";
    progress = 0;
    render();

    const fd = new FormData();
    fd.append("file", file);
    fd.append("consent", "true");
    fd.append("engine", selectedEngine);
    fd.append("compact_silence", compactSilence ? "true" : "false");
    fd.append("review", review ? "true" : "false");

    try {
      const res = await api.uploadSession(fd, (ratio) => {
        progress = ratio;
        render();
      });
      navigate(`/aulas/${res.id}`);
    } catch (err) {
      uploading = false;
      errorMessage = err.message || "Falha no envio da aula.";
      render();
    }
  }

  function render() {
    const uploadIcon = [
      "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12",
    ];

    const errorAlert = errorMessage
      ? h("div", { class: "alert", role: "alert" }, errorMessage)
      : null;

    let fileSection;
    if (file) {
      fileSection = h(
        "div",
        { class: "file-chip" },
        h(
          "div",
          {},
          h("strong", {}, file.name),
          h("div", { class: "hint" }, formatBytes(file.size))
        ),
        uploading
          ? null
          : h(
              "button",
              {
                type: "button",
                class: "button button-sm button-ghost",
                onClick: () => {
                  file = null;
                  render();
                },
              },
              "Trocar arquivo"
            )
      );
    } else {
      const fileInput = h("input", {
        type: "file",
        id: "audio-file-input",
        accept: allowedExts.join(","),
        onChange: (e) => {
          if (e.target.files && e.target.files[0]) {
            handleFileSelection(e.target.files[0]);
          }
        },
      });

      fileSection = h(
        "label",
        {
          class: "dropzone",
          htmlFor: "audio-file-input",
          onDragover: (e) => {
            e.preventDefault();
            e.currentTarget.classList.add("is-over");
          },
          onDragleave: (e) => {
            e.currentTarget.classList.remove("is-over");
          },
          onDrop: (e) => {
            e.preventDefault();
            e.currentTarget.classList.remove("is-over");
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFileSelection(e.dataTransfer.files[0]);
            }
          },
        },
        fileInput,
        svgIcon(uploadIcon, "dropzone-icon"),
        h("div", { class: "dropzone-title" }, "Arraste a gravação aqui ou ", h("u", {}, "procure no computador")),
        h("div", { class: "hint" }, `Formatos aceitos: ${allowedExts.slice(0, 5).join(", ")}, etc. Até 300 MB e até 3 horas.`)
      );
    }

    const consentCheckbox = h("input", {
      type: "checkbox",
      id: "consent-check",
      checked: consentGiven,
      disabled: uploading,
      onChange: (e) => {
        consentGiven = e.target.checked;
        render();
      },
    });

    const consentBlock = h(
      "div",
      {
        style: {
          padding: "14px 16px",
          border: "1.5px solid var(--rule)",
          borderRadius: "var(--radius-sm)",
          background: "var(--paper-soft)",
          display: "grid",
          gap: "8px",
        },
      },
      h(
        "label",
        {
          style: {
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            fontWeight: "600",
            cursor: "pointer",
          },
        },
        consentCheckbox,
        h("span", {}, "Tenho autorização dos alunos (ou dos responsáveis) para gravar e processar esta aula.")
      ),
      h("p", { class: "hint", style: { margin: "0", paddingLeft: "26px" } }, "O áudio e o texto da aula são processados pelo Google Gemini.")
    );

    let progressSection = null;
    if (uploading) {
      const pct = Math.round(progress * 100);
      progressSection = h(
        "div",
        { style: { display: "grid", gap: "6px" } },
        h("div", { class: "progress" }, h("span", { style: { width: `${pct}%` } })),
        h("div", { class: "hint", style: { textAlign: "right" } }, `${pct}% enviado...`)
      );
    }

    const submitBtn = h(
      "button",
      {
        type: "submit",
        class: "button button-primary button-block",
        disabled: !file || !consentGiven || uploading,
      },
      uploading ? "Enviando gravação..." : "Transcrever a aula"
    );

    const form = h(
      "form",
      {
        class: "card upload",
        style: { margin: "0 auto" },
        onSubmit: handleSubmit,
      },
      h("div", { class: "page-head", style: { marginBottom: "4px" } },
        h("div", {},
          h("h1", {}, "Nova aula"),
          h("p", { class: "lead" }, "Envie a gravação de áudio ou vídeo da sua aula de inglês.")
        )
      ),
      errorAlert,
      fileSection,
      h(
        "details",
        { class: "more" },
        h("summary", {}, "Opções avançadas"),
        h(
          "div",
          { style: { display: "grid", gap: "12px", marginTop: "12px" } },
          h(
            "label",
            { class: "toggle" },
            h("div", { class: "toggle-text" },
              h("div", { class: "toggle-title" }, "Compactar pausas longas"),
              h("div", { class: "hint" }, "Remove silêncios de mais de 1,5s para acelerar a transcrição.")
            ),
            h("input", {
              type: "checkbox",
              checked: compactSilence,
              disabled: uploading,
              onChange: (e) => { compactSilence = e.target.checked; },
            })
          ),
          h(
            "label",
            { class: "toggle" },
            h("div", { class: "toggle-text" },
              h("div", { class: "toggle-title" }, "Descobrir nomes dos alunos pela IA"),
              h("div", { class: "hint" }, "Identifica quando os alunos se apresentam ou são chamados pelo nome.")
            ),
            h("input", {
              type: "checkbox",
              checked: review,
              disabled: uploading,
              onChange: (e) => { review = e.target.checked; },
            })
          )
        )
      ),
      consentBlock,
      progressSection,
      submitBtn
    );

    v.replaceChildren(form);
  }

  render();
}
