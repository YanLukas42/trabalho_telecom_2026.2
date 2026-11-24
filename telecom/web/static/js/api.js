"use strict";

/* Pauta: cliente de API v1 centralizado. */

import { detailText } from "./format.js";

async function parseError(response) {
  try {
    const data = await response.json();
    return detailText(data) || `Erro ${response.status}: ${response.statusText}`;
  } catch {
    return `Erro ${response.status}: ${response.statusText}`;
  }
}

export const api = {
  async request(path, options = {}) {
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    const config = {
      credentials: "same-origin",
      headers,
      ...options,
    };
    const response = await fetch(path, config);
    if (!response.ok) {
      const err = new Error(await parseError(response));
      err.status = response.status;
      throw err;
    }
    return response.json();
  },

  login: (credentials) =>
    api.request("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    }),

  logout: () =>
    api.request("/api/v1/auth/logout", {
      method: "POST",
    }),

  me: () => api.request("/api/v1/me"),

  config: () => api.request("/api/v1/config"),

  sessions: () => api.request("/api/v1/sessions"),

  session: (id) => api.request(`/api/v1/sessions/${encodeURIComponent(id)}`),

  deleteSession: (id) =>
    api.request(`/api/v1/sessions/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  retrySession: (id) =>
    api.request(`/api/v1/sessions/${encodeURIComponent(id)}/retry`, {
      method: "POST",
    }),

  updateParticipants: (id, participants) =>
    api.request(`/api/v1/sessions/${encodeURIComponent(id)}/participants`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(participants),
    }),

  createLesson: (id, body) =>
    api.request(`/api/v1/sessions/${encodeURIComponent(id)}/lesson`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  saveLesson: (id, lesson) =>
    api.request(`/api/v1/sessions/${encodeURIComponent(id)}/lesson`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lesson),
    }),

  mediaUrl: (id) => `/api/v1/sessions/${encodeURIComponent(id)}/media`,

  fileUrl: (id, kind) => `/api/v1/sessions/${encodeURIComponent(id)}/files/${encodeURIComponent(kind)}`,

  /* XHR em vez de fetch para acompanhar o progresso de upload */
  uploadSession(formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/v1/sessions");
      xhr.responseType = "json";
      xhr.withCredentials = true;

      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress(event.loaded / event.total);
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(xhr.response);
        } else {
          const msg = detailText(xhr.response) || `Erro ${xhr.status}`;
          const err = new Error(msg);
          err.status = xhr.status;
          reject(err);
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error("Sem conexão com o servidor. Confira se ele está rodando."));
      });

      xhr.send(formData);
    });
  },
};
