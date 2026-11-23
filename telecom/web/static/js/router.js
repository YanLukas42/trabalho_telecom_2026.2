"use strict";

/* Pauta: roteamento baseado em hash (#/...) sem recarregar a página. */

export function parseRoute(hash) {
  const raw = (hash || "#/").replace(/^#/, "");
  const path = raw.startsWith("/") ? raw : "/" + raw;

  if (path === "/entrar") {
    return { name: "login", params: {} };
  }
  if (path === "/" || path === "") {
    return { name: "sessions", params: {} };
  }
  if (path === "/nova") {
    return { name: "upload", params: {} };
  }

  const matchSession = path.match(/^\/aulas\/([a-zA-Z0-9_\-]+)(?:\/(atividades|proxima))?\/?$/);
  if (matchSession) {
    const [, id, sub] = matchSession;
    if (sub === "atividades") {
      return { name: "sheets", params: { id } };
    }
    if (sub === "proxima") {
      return { name: "plan", params: { id } };
    }
    return { name: "session", params: { id } };
  }

  // Compatibilidade com links antigos (#/jobs/...)
  const matchJob = path.match(/^\/jobs\/([a-zA-Z0-9_\-]+)(?:\/(atividades|proxima))?\/?$/);
  if (matchJob) {
    const [, id, sub] = matchJob;
    if (sub === "atividades") return { name: "sheets", params: { id } };
    if (sub === "proxima") return { name: "plan", params: { id } };
    return { name: "session", params: { id } };
  }

  return { name: "not_found", params: { path } };
}

export function navigate(path) {
  const hash = path.startsWith("#") ? path : `#${path.startsWith("/") ? path : "/" + path}`;
  if (window.location.hash === hash) {
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = hash;
  }
}
