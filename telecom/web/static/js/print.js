"use strict";

/* Pauta: preparação de documentos para impressão limpa em PDF.
   Copia só os nós selecionados para #print-root; o CSS esconde o resto.
   O document.title vira o nome sugerido para o arquivo PDF gerado. */

export function printDocuments(title, nodes) {
  const root = document.getElementById("print-root");
  if (!root) return;
  const previousTitle = document.title;
  root.replaceChildren(...nodes);
  document.title = title;
  document.body.classList.add("printing");

  const cleanup = () => {
    document.body.classList.remove("printing");
    document.title = previousTitle;
    root.replaceChildren();
  };

  window.addEventListener("afterprint", cleanup, { once: true });
  window.print();
}
