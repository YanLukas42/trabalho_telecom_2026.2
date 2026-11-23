"use strict";

/* Pauta: tela de login (#/entrar). */

import { api } from "../api.js";
import { h, view } from "../dom.js";

export function renderLogin({ onSuccess }) {
  const v = view();
  let loading = false;
  let errorMessage = "";

  function render() {
    const errorAlert = errorMessage
      ? h("div", { class: "alert", role: "alert" }, errorMessage)
      : null;

    const emailInput = h("input", {
      type: "email",
      name: "email",
      id: "login-email",
      class: "search",
      style: { width: "100%" },
      required: true,
      autocomplete: "username",
      placeholder: "exemplo@escola.com.br",
      disabled: loading,
    });

    const passwordInput = h("input", {
      type: "password",
      name: "password",
      id: "login-password",
      class: "search",
      style: { width: "100%" },
      required: true,
      autocomplete: "current-password",
      placeholder: "Sua senha de acesso",
      disabled: loading,
    });

    const submitBtn = h(
      "button",
      {
        type: "submit",
        class: "button button-primary button-block",
        disabled: loading,
      },
      loading ? "Entrando..." : "Entrar"
    );

    const form = h(
      "form",
      {
        class: "card",
        style: { maxWidth: "420px", margin: "48px auto", padding: "32px 28px", display: "grid", gap: "20px" },
        onSubmit: async (e) => {
          e.preventDefault();
          const email = emailInput.value.trim();
          const password = passwordInput.value;
          if (!email || !password) return;

          loading = true;
          errorMessage = "";
          render();

          try {
            const user = await api.login({ email, password });
            onSuccess(user);
          } catch (err) {
            errorMessage = err.message || "E-mail ou senha incorretos.";
            loading = false;
            render();
          }
        },
      },
      h("h1", { style: { fontSize: "26px", marginBottom: "4px" } }, "Entrar na Pauta"),
      h("p", { class: "hint" }, "Use o e-mail e a senha cadastrados pelo administrador da sua escola."),
      errorAlert,
      h("div", { class: "field" },
        h("label", { for: "login-email" }, "E-mail"),
        emailInput
      ),
      h("div", { class: "field" },
        h("label", { for: "login-password" }, "Senha"),
        passwordInput
      ),
      submitBtn
    );

    v.replaceChildren(form);
    setTimeout(() => emailInput.focus(), 50);
  }

  render();
}
