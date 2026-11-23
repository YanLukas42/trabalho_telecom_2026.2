"use strict";

/* Pauta: ponto de entrada da aplicação (módulo ES puro, sem bundler). */

import { api } from "./api.js";
import { clear, h, topbar, view } from "./dom.js";
import { navigate, parseRoute } from "./router.js";
import { renderLogin } from "./views/login.js";
import { renderPlan } from "./views/plan.js";
import { renderSession } from "./views/session.js";
import { renderSessions } from "./views/sessions.js";
import { renderSheets } from "./views/sheets.js";
import { renderUpload } from "./views/upload.js";

const state = {
  user: null,
  config: null,
  currentCleanup: null,
};

function renderTopbar() {
  const tb = topbar();
  if (!tb) return;

  const brandMark = h(
    "svg",
    { class: "brand-mark", viewBox: "0 0 24 24", "aria-hidden": "true" },
    h("rect", { width: "24", height: "24", rx: "6" }),
    h("path", { class: "mark-rules", d: "M6 8h12M6 12h12M6 16h7" }),
    h("path", { class: "mark-tick", d: "M16 15l2 2 3-4" })
  );

  const brand = h(
    "a",
    {
      class: "brand",
      href: state.user ? "#/" : "#/entrar",
      onClick: (e) => {
        e.preventDefault();
        navigate(state.user ? "/" : "/entrar");
      },
    },
    brandMark,
    h("span", {}, "Pauta")
  );

  if (!state.user) {
    tb.replaceChildren(brand);
    return;
  }

  const currentHash = window.location.hash || "#/";

  const navLeft = h(
    "div",
    { style: { display: "flex", alignItems: "center", gap: "20px" } },
    brand,
    h(
      "a",
      {
        class: "topbar-link",
        style: {
          color: currentHash === "#/" ? "#fff" : "rgba(255, 255, 255, 0.75)",
          fontWeight: currentHash === "#/" ? "700" : "500",
          textDecoration: "none",
        },
        href: "#/",
        onClick: (e) => {
          e.preventDefault();
          navigate("/");
        },
      },
      "Minhas aulas"
    ),
    h(
      "a",
      {
        class: "topbar-link",
        style: {
          color: currentHash === "#/nova" ? "#fff" : "rgba(255, 255, 255, 0.75)",
          fontWeight: currentHash === "#/nova" ? "700" : "500",
          textDecoration: "none",
        },
        href: "#/nova",
        onClick: (e) => {
          e.preventDefault();
          navigate("/nova");
        },
      },
      "Nova aula"
    )
  );

  const schoolName = h(
    "span",
    {
      class: "hint",
      style: { color: "rgba(255, 255, 255, 0.85)", fontWeight: "600" },
    },
    state.user.school_name || ""
  );

  const logoutBtn = h(
    "button",
    {
      class: "button button-ghost button-sm",
      style: { color: "#fff" },
      onClick: async () => {
        try {
          await api.logout();
        } catch (e) {
          console.error("Erro ao deslogar:", e);
        }
        state.user = null;
        renderTopbar();
        navigate("/entrar");
      },
    },
    "Sair"
  );

  const navRight = h(
    "div",
    { style: { display: "flex", alignItems: "center", gap: "16px" } },
    schoolName,
    logoutBtn
  );

  tb.replaceChildren(navLeft, navRight);
}

async function handleRoute() {
  if (state.currentCleanup) {
    try {
      state.currentCleanup();
    } catch {}
    state.currentCleanup = null;
  }

  renderTopbar();

  const route = parseRoute(window.location.hash);

  // Se não estiver autenticado e não for a tela de login, tenta buscar perfil ou manda pro login
  if (!state.user && route.name !== "login") {
    try {
      state.user = await api.me();
      if (!state.config) {
        state.config = await api.config().catch(() => null);
      }
      renderTopbar();
    } catch {
      navigate("/entrar");
      return;
    }
  }

  // Se já estiver autenticado e tentar ir para /entrar, redireciona para a home
  if (state.user && route.name === "login") {
    navigate("/");
    return;
  }

  switch (route.name) {
    case "login":
      renderLogin({
        onSuccess: async (user) => {
          state.user = user;
          try {
            state.config = await api.config();
          } catch {}
          renderTopbar();
          navigate("/");
        },
      });
      break;

    case "sessions":
      state.currentCleanup = renderSessions({
        me: state.user,
        onNavigate: navigate,
      });
      break;

    case "upload":
      renderUpload({ config: state.config });
      break;

    case "session":
      state.currentCleanup = renderSession({ id: route.params.id, activeTab: "aula" });
      break;

    case "sheets":
      renderSheets({ id: route.params.id });
      break;

    case "plan":
      renderPlan({ id: route.params.id });
      break;

    default:
      view().replaceChildren(
        h(
          "div",
          { class: "card state", style: { padding: "40px" } },
          h("h2", {}, "Página não encontrada"),
          h("p", { class: "hint" }, "O endereço acessado não existe."),
          h(
            "a",
            {
              class: "button button-primary",
              style: { marginTop: "16px" },
              href: "#/",
              onClick: (e) => {
                e.preventDefault();
                navigate("/");
              },
            },
            "Voltar para Minhas aulas"
          )
        )
      );
      break;
  }
}

async function init() {
  window.addEventListener("hashchange", handleRoute);

  // Tenta verificar sessão ativa no boot
  try {
    state.user = await api.me();
    state.config = await api.config().catch(() => null);
  } catch {
    state.user = null;
  }

  renderTopbar();
  handleRoute();
}

init();
