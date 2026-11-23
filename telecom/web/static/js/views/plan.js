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
    const title = `Plano da próxima aula, ${session.file_name}`;
    const doc = renderPlanPaper(plan);
    printDocuments(title, [doc]);
  }

  function renderPlanPaper(plan) {
    const stageItems = (plan.stages || []).map((stage) =>
      h("li", { class: "plan-block" },
        h("div", { class: "plan-min" },
          `${stage.minutes}`,
          h("small", {}, "minutos")
        ),
        h("div", {},
          h("h4", {}, stage.name),
          h("p", {}, stage.activity)
        )
      )
    );

    const topics = (plan.review_topics || []).map((t) => h("li", {}, t));

    return h("div", { class: "paper" },
      h("div", { class: "paper-head" },
        h("h3", {}, "Plano da próxima aula"),
        h("span", { class: "hint" }, session.file_name)
      ),
      h("div", { style: { marginBottom: "16px" } },
        h("strong", {}, "Nível da turma: "),
        h("span", {}, plan.class_level)
      ),
      h("div", { style: { marginBottom: "16px" } },
        h("strong", {}, "Objetivo: "),
        h("p", { class: "lead" }, plan.goal)
      ),
      topics.length > 0
        ? h("div", { style: { marginBottom: "20px" } },
            h("h4", {}, "Tópicos a retomar"),
            h("ul", { class: "topic-list", style: { marginTop: "8px" } }, topics)
          )
        : null,
      h("div", { style: { marginBottom: "20px" } },
        h("h4", {}, "Etapas da aula"),
        h("ul", { class: "plan-blocks", style: { marginTop: "8px" } }, stageItems)
      ),
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
        session.has_lesson ? h("span", { class: "tab-badge" }, "pronto") : null
      ),
      h("a", { class: "tab", "aria-selected": "true", href: `#/aulas/${id}/proxima` }, "Próxima aula")
    );

    let content;
    const plan = session?.lesson?.plan;
    if (!plan) {
      content = h(
        "div",
        { class: "card state" },
        h("h2", { style: { fontSize: "20px" } }, "Nenhum plano gerado ainda"),
        h("p", { class: "hint" }, "Gere as atividades da aula primeiro para criar o plano pedagógico da próxima aula."),
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
