"use strict";

/* Utilitários de formatação e texto da Pauta. */

export function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return "00:00";
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const remSec = s % 60;
  if (m >= 60) {
    const h = Math.floor(m / 60);
    const remMin = m % 60;
    return `${String(h).padStart(2, "0")}:${String(remMin).padStart(2, "0")}:${String(remSec).padStart(2, "0")}`;
  }
  return `${String(m).padStart(2, "0")}:${String(remSec).padStart(2, "0")}`;
}

export function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return "--";
  const totalMin = Math.round(seconds / 60);
  if (totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function formatDate(val) {
  if (!val) return "--";
  const d = typeof val === "number" ? new Date(val * 1000) : new Date(val);
  if (isNaN(d.getTime())) return String(val);
  return d.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0 B";
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(1)} MB`;
  const kb = bytes / 1024;
  return `${kb.toFixed(0)} KB`;
}

export function detailText(data) {
  if (!data) return "";
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((err) => err.msg || JSON.stringify(err)).join(", ");
  }
  return "";
}
