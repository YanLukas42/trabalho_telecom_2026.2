"use strict";

/* Pauta: tela de plano da próxima aula (#/aulas/<id>/proxima). */

import { api } from "../api.js";
import { h, view } from "../dom.js";
import { printDocuments } from "../print.js";
import { navigate } from "../router.js";

export function renderPlan({ id }) {
  const v = view();

  let session = null;
  let loading = true;
  let errorMessage = "";

  async function loadData() {
    try {
      session = await api.session(id);
    } catch (err) {
      errorMessage = err.message || "Erro ao carregar o plano da aula.";
    } finally {
      loading = false;
      render();
    }
  }

  function handlePrintPlan() {
    const plan = session?.lesson?.plan;
    if (!plan) return;
    printDocuments(`Plano da próxima aula, ${session.file_name}`, [renderPlanPaper(plan)]);
  }

  function renderPlanPaper(plan) {
    const blockItems = (plan.blocks || []).map((block) =>
      h("li", { class: "plan-block" },
        h("div", { class: "plan-min" },
          `${block.minutes}`,
          h("small", {}, "min")
        ),
        h("div", {},
          h("h4", {}, block.title),
          h("p", {}, block.description)
        )
      )
    );

    const topics = (plan.topics || []).map((t) => h("li", {}, t));

    return h("div", { class: "paper" },
      h("div", { class: "paper-head" },
        h("h3", {}, "Plano da próxima aula"),
        h("span", { class: "hint" }, session.file_name)
      ),
      plan.objective
        ? h("div", { style: { marginBottom: "16px" } },
            h("strong", {}, "Objetivo: "),
            h("p", { class: "lead" }, plan.objective)
          )
        : null,
      topics.length > 0
        ? h("div", { style: { marginBottom: "20px" } },
            h("h4", {}, "Tópicos a retomar"),
            h("ul", { class: "topic-list", style: { marginTop: "8px" } }, topics)
          )
        : null,
      blockItems.length > 0
        ? h("div", { style: { marginBottom: "20px" } },
            h("h4", {}, "Etapas da aula"),
            h("ul", { class: "plan-blocks", style: { marginTop: "8px" } }, blockItems)
          )
        : null,
      plan.homework
        ? h("div", { style: { marginTop: "16px" } },
            h("h4", {}, "Tarefa de casa"),
            h("p", {}, plan.homework)
          )
        : null
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
      h("a", { class: "tab", href: `#/aulas/${id}/atividades`, onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}/atividades`); } },
        "Atividades",
        session?.has_lesson ? h("span", { class: "tab-badge" }, "pronto") : null
      ),
      h("a", { class: "tab", "aria-selected": "true", href: `#/aulas/${id}/proxima` }, "Próxima aula")
    );

    if (errorMessage) {
      v.replaceChildren(navTabs, h("div", { class: "alert" }, errorMessage));
      return;
    }

    const plan = session?.lesson?.plan;
    let content;
    if (!plan) {
      content = h(
        "div",
        { class: "card state" },
        h("h2", { style: { fontSize: "20px" } }, "Nenhum plano gerado ainda"),
        h("p", { class: "hint" }, "Gere as atividades da aula primeiro para criar o plano da próxima aula."),
        h("a", {
          class: "button button-primary",
          style: { marginTop: "16px" },
          href: `#/aulas/${id}/atividades`,
          onClick: (e) => { e.preventDefault(); navigate(`/aulas/${id}/atividades`); },
        }, "Ir para Atividades")
      );
    } else {
      const printBtn = h(
        "div",
        { style: { display: "flex", justifyContent: "flex-end", marginBottom: "16px" } },
        h("button", { class: "button", onClick: handlePrintPlan }, "Imprimir plano")
      );
      content = h("div", {}, printBtn, renderPlanPaper(plan));
    }

    v.replaceChildren(navTabs, content);
  }

  loadData();
}
