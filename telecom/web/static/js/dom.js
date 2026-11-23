"use strict";

/* Pauta: manipulação segura do DOM sem framework.
   Texto de aluno e da IA é sempre renderizado como textNode. */

export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith("on")) {
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key === "class") {
      el.className = value;
    } else if (key === "style" && typeof value === "object") {
      for (const [prop, val] of Object.entries(value)) {
        el.style.setProperty(prop.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`), val);
      }
    } else if (key in el && typeof value !== "string") {
      el[key] = value;
    } else {
      el.setAttribute(key, value === true ? "" : value);
    }
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

export function svgIcon(paths, className = "dropzone-icon") {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", className);
  svg.setAttribute("aria-hidden", "true");
  for (const d of paths) {
    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

export function view() {
  return document.getElementById("view");
}

export function topbar() {
  return document.getElementById("topbar");
}

export function clear(el) {
  if (el) el.replaceChildren();
}
