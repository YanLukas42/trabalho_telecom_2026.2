"use strict";

/* Pauta: tela de folhas de atividades individuais (#/aulas/<id>/atividades).
   Permite gerar material com IA, editar erros e exercícios (US-13) e imprimir em PDF. */

import { api } from "../api.js";
import { h, view } from "../dom.js";
import { printDocuments } from "../print.js";
import { navigate } from "../router.js";

const DEFAULT_LEVEL = "B1";
const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

function fld(label, input) {
  return h("div", { class: "field" }, h("label", {}, label), input);
}

export function renderSheets({ id }) {
  const v = view();

  let session = null;
  let loading = true;
  let generating = false;
  let saving = false;
  let isEditing = false;
  let errorMessage = "";
  let successMessage = "";
  let showForm = false;

  let selectedLevel = DEFAULT_LEVEL;
  let exercisesCount = 5;
  let focusText = "";

  async function loadData() {
    try {
      session = await api.session(id);
      errorMessage = "";
      showForm = !session.lesson;
    } catch (err) {
      errorMessage = err.message || "Erro ao carregar atividades.";
    } finally {
      loading = false;
      render();
    }
  }

  async function handleGenerate(e) {
    e.preventDefault();
    generating = true;
    errorMessage = "";
    render();

    const parts = (session.participants || []).map((p) => ({ label: p.label, name: p.name, role: p.role }));
    try {
      const lesson = await api.createLesson(id, {
        level: selectedLevel,
        exercises_per_student: Number(exercisesCount) || 5,
        focus: focusText.trim(),
        participants: parts,
      });
      session.lesson = lesson;
      session.has_lesson = true;
      showForm = false;
      isEditing = false;
    } catch (err) {
      errorMessage = err.message || "Não foi possível gerar as atividades.";
    } finally {
      generating = false;
      render();
    }
  }

  async function handleSaveEdits() {
    saving = true;
    errorMessage = "";
    successMessage = "";
    render();
    try {
      await api.saveLesson(id, session.lesson);
      isEditing = false;
      successMessage = "Alterações salvas com sucesso!";
      setTimeout(() => { successMessage = ""; render(); }, 3000);
    } catch (err) {
      errorMessage = err.message || "Falha ao salvar as alterações do material.";
    } finally {
      saving = false;
      render();
    }
  }

  function printAllSheets() {
    if (!session?.lesson) return;
    printDocuments(`Atividades, ${session.file_name}`, session.lesson.sheets.map((s) => renderPaper(s, false)));
  }

  function printAnswerKey() {
    if (!session?.lesson?.answer_key) return;
    const keyItems = session.lesson.answer_key.map((item) =>
      h("div", { style: { marginBottom: "16px" } },
        h("h4", {}, item.student_name),
        h("ul", { class: "exercises" }, item.items.map((ex) => h("li", {}, h("strong", {}, ex.prompt), h("div", { class: "answer" }, ex.answer))))
      )
    );
    printDocuments(`Gabarito, ${session.file_name}`, [
      h("div", { class: "paper" }, h("div", { class: "paper-head" }, h("h3", {}, `Gabarito — ${session.file_name}`)), h("div", {}, keyItems))
    ]);
  }

  function renderPaper(sheet, forEdit = false) {
    let reviewSection;
    if (forEdit) {
      const mistakeItems = sheet.mistakes.map((m, mIdx) =>
        h("div", { class: "card", style: { padding: "10px", display: "grid", gap: "6px" } },
          fld("Fala do aluno:", h("input", { type: "text", value: m.quote, onInput: (e) => { m.quote = e.target.value; } })),
          fld("Forma correta:", h("input", { type: "text", value: m.correction, onInput: (e) => { m.correction = e.target.value; } })),
          fld("Explicação:", h("input", { type: "text", value: m.explanation, onInput: (e) => { m.explanation = e.target.value; } })),
          h("button", {
            type: "button",
            class: "button button-sm button-ghost",
            style: { justifySelf: "start", color: "var(--pen)" },
            onClick: () => { sheet.mistakes.splice(mIdx, 1); render(); },
          }, "Remover erro")
        )
      );
      reviewSection = h("div", {}, h("h4", {}, "O que revisar"), h("div", { style: { display: "grid", gap: "10px" } }, mistakeItems));
    } else {
      const reviewItems = sheet.mistakes.map((m) =>
        h("li", { class: "review-item" },
          h("div", {}, h("del", {}, m.quote), " → ", h("ins", {}, m.correction)),
          h("div", { class: "why" }, m.explanation)
        )
      );
      reviewSection = sheet.mistakes.length > 0
        ? h("div", {}, h("h4", {}, "O que revisar"), h("ul", { class: "review-list" }, reviewItems))
        : null;
    }

    let exercisesSection;
    if (forEdit) {
      const exItems = sheet.exercises.map((ex, eIdx) => {
        const typeSelect = h("select", {
          onChange: (e) => { ex.type = e.target.value; render(); },
        },
          h("option", { value: "multiple_choice", selected: ex.type === "multiple_choice" }, "Múltipla escolha"),
          h("option", { value: "rewrite", selected: ex.type === "rewrite" }, "Reescrita"),
          h("option", { value: "short_answer", selected: ex.type === "short_answer" }, "Resposta curta")
        );

        let optionsField = null;
        if (ex.type === "multiple_choice") {
          optionsField = fld("Opções (uma por linha):", h("textarea", {
            rows: 3,
            value: (ex.options || []).join("\n"),
            onInput: (e) => { ex.options = e.target.value.split("\n").map((s) => s.trim()).filter(Boolean); },
          }));
        }

        return h("div", { class: "card", style: { padding: "12px", display: "grid", gap: "8px" } },
          fld(`Exercício ${eIdx + 1} - Enunciado:`, h("input", { type: "text", value: ex.prompt, onInput: (e) => { ex.prompt = e.target.value; } })),
          fld("Tipo:", typeSelect),
          optionsField,
          fld("Resposta esperada:", h("input", { type: "text", value: ex.answer, onInput: (e) => { ex.answer = e.target.value; } })),
          h("button", {
            type: "button",
            class: "button button-sm button-ghost",
            style: { justifySelf: "start", color: "var(--pen)" },
            onClick: () => { sheet.exercises.splice(eIdx, 1); render(); },
          }, "Remover atividade")
        );
      });

      exercisesSection = h("div", { style: { marginTop: "16px" } },
        h("h4", {}, "Atividades"),
        h("div", { style: { display: "grid", gap: "12px" } }, exItems),
        h("button", {
          type: "button",
          class: "button button-sm",
          style: { marginTop: "10px" },
          onClick: () => {
            sheet.exercises.push({ prompt: "Complete the sentence:", type: "short_answer", options: [], answer: "" });
            render();
          },
        }, "+ Adicionar atividade")
      );
    } else {
      const exItems = sheet.exercises.map((ex) => {
        const optEl = ex.type === "multiple_choice" && ex.options?.length
          ? h("ol", { class: "ex-options" }, ex.options.map((opt) => h("li", {}, opt)))
          : h("div", {}, h("span", { class: "write-line" }), h("span", { class: "write-line" }));

        return h("li", {},
          h("div", { class: "ex-prompt" }, ex.prompt),
          optEl,
          h("div", { class: "answer" }, h("span", {}, "Resposta:"), ex.answer)
        );
      });

      exercisesSection = h("div", {}, h("h4", {}, "Atividades"), h("ol", { class: "exercises" }, exItems));
    }

    return h("div", { class: "paper", style: { marginBottom: "24px" } },
      h("div", { class: "paper-head" },
        h("h3", {}, sheet.student_name),
        h("span", { class: "hint" }, session.lesson?.school_name || "Pauta")
      ),
      sheet.strength ? h("div", { class: "strength" }, `Ponto forte: ${sheet.strength}`) : null,
      reviewSection,
      exercisesSection
    );
  }

  function render() {
    if (loading) {
      v.replaceChildren(h("div", { class: "card state" }, h("div", { class: "spinner" }), h("p", {}, "Carregando...")));
      return;
    }

    const navTabs = h(
      "div",
      { class: "tabs" },
      h("a", { class: "tab", href: `#/aulas/${id}`, onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}`); } }, "Aula"),
      h("a", { class: "tab", "aria-selected": "true", href: `#/aulas/${id}/atividades` },
        "Atividades",
        session.has_lesson ? h("span", { class: "tab-badge" }, "pronto") : null
      ),
      h("a", { class: "tab", href: `#/aulas/${id}/proxima`, onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}/proxima`); } }, "Próxima aula")
    );

    const errorAlert = errorMessage ? h("div", { class: "alert", style: { marginBottom: "16px" } }, errorMessage) : null;
    const successAlert = successMessage ? h("div", { class: "notice", style: { marginBottom: "16px" } }, successMessage) : null;

    let content;
    if (showForm) {
      content = h(
        "form",
        { class: "card maker", onSubmit: handleGenerate },
        h("h2", { style: { fontSize: "20px" } }, "Criar atividades e plano da aula"),
        h("p", { class: "hint" }, "Gera uma folha de atividades sob medida para cada aluno e um roteiro para a próxima aula."),
        fld("Nível da turma:", h("select", {
          id: "lesson-level",
          value: selectedLevel,
          onChange: (e) => { selectedLevel = e.target.value; },
        }, LEVELS.map((lvl) => h("option", { value: lvl, selected: lvl === selectedLevel }, lvl)))),
        fld("Atividades por aluno (3 a 10):", h("input", {
          type: "number",
          id: "lesson-ex-count",
          min: 3,
          max: 10,
          value: exercisesCount,
          onInput: (e) => { exercisesCount = e.target.value; },
        })),
        fld("Foco da próxima aula (opcional):", h("textarea", {
          id: "lesson-focus",
          placeholder: "Ex.: Revisar Simple Past e focar em verbos irregulares...",
          value: focusText,
          onInput: (e) => { focusText = e.target.value; },
        })),
        h("div", { class: "notice" }, "A IA lê só o texto da transcrição, sem ouvir o áudio. Confira o material antes de entregar."),
        h("div", { class: "maker-actions" },
          h("button", {
            type: "submit",
            class: "button button-primary",
            disabled: generating,
          }, generating ? "Criando o material..." : "Criar atividades e plano")
        )
      );
    } else {
      const sheetsList = (session.lesson?.sheets || []).map((sheet) => renderPaper(sheet, isEditing));
      const actionButtons = h(
        "div",
        { class: "sheet-actions", style: { marginBottom: "20px" } },
        h("div", { style: { display: "flex", gap: "8px", flexWrap: "wrap" } },
          isEditing
            ? h("button", { class: "button button-primary", disabled: saving, onClick: handleSaveEdits }, saving ? "Salvando..." : "Salvar alterações")
            : h("button", { class: "button", onClick: () => { isEditing = true; render(); } }, "Editar material"),
          isEditing ? h("button", { class: "button button-ghost", onClick: () => { isEditing = false; render(); } }, "Cancelar edição") : null
        ),
        !isEditing
          ? h("div", { style: { display: "flex", gap: "8px", flexWrap: "wrap" } },
              h("button", { class: "button", onClick: printAllSheets }, "Imprimir todas as folhas"),
              h("button", { class: "button button-ghost", onClick: printAnswerKey }, "Imprimir gabarito"),
              h("button", { class: "button button-ghost", onClick: () => { showForm = true; render(); } }, "Gerar de novo")
            )
          : null
      );
      content = h("div", {}, actionButtons, sheetsList);
    }

    v.replaceChildren(navTabs, errorAlert, successAlert, content);
  }

  loadData();
}
