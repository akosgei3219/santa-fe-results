// src/index.jsx
import React from "react";
import { jsx, jsxs } from "react/jsx-runtime";
function Root({ children, style, ...rest }) {
  return /* @__PURE__ */ jsx("div", { className: "sfhm-root", style, ...rest, children });
}
function Button({ variant = "solid", href, children, className = "", ...rest }) {
  const cls = `sfhm-btn${variant === "ghost" ? " sfhm-btn--ghost" : ""} ${className}`.trim();
  if (href) {
    return /* @__PURE__ */ jsx("a", { className: cls, href, ...rest, children });
  }
  return /* @__PURE__ */ jsx("button", { type: "button", className: cls, ...rest, children });
}
function Card({ padded = false, children, className = "", ...rest }) {
  const cls = `sfhm-card${padded ? " sfhm-card--padded" : ""} ${className}`.trim();
  return /* @__PURE__ */ jsx("div", { className: cls, ...rest, children });
}
function SectionHeader({ eyebrow, title, sub, ...rest }) {
  return /* @__PURE__ */ jsxs("header", { ...rest, children: [
    eyebrow && /* @__PURE__ */ jsx("p", { className: "sfhm-eyebrow", children: eyebrow }),
    /* @__PURE__ */ jsx("h2", { className: "sfhm-section-title", children: title }),
    sub && /* @__PURE__ */ jsx("p", { className: "sfhm-section-sub", children: sub })
  ] });
}
function Stat({ value, label, ...rest }) {
  return /* @__PURE__ */ jsxs("div", { className: "sfhm-stat", ...rest, children: [
    /* @__PURE__ */ jsx("b", { children: value }),
    /* @__PURE__ */ jsx("span", { children: label })
  ] });
}
function StatStrip({ children, ...rest }) {
  return /* @__PURE__ */ jsx("div", { className: "sfhm-stat-strip", ...rest, children });
}
function Chip({ title, detail, ...rest }) {
  return /* @__PURE__ */ jsxs("span", { className: "sfhm-chip", ...rest, children: [
    /* @__PURE__ */ jsx("b", { children: title }),
    /* @__PURE__ */ jsx("span", { children: detail })
  ] });
}
function CountdownCell({ value, label, ...rest }) {
  return /* @__PURE__ */ jsxs("span", { className: "sfhm-count-cell", ...rest, children: [
    /* @__PURE__ */ jsx("b", { children: value }),
    /* @__PURE__ */ jsx("span", { children: label })
  ] });
}
function FAQItem({ question, defaultOpen = false, children, ...rest }) {
  return /* @__PURE__ */ jsxs("details", { className: "sfhm-faq-item", open: defaultOpen || void 0, ...rest, children: [
    /* @__PURE__ */ jsx("summary", { children: question }),
    /* @__PURE__ */ jsx("div", { className: "sfhm-faq-answer", children })
  ] });
}
function PromoBar({ children, ...rest }) {
  return /* @__PURE__ */ jsx("div", { className: "sfhm-promo-bar", ...rest, children });
}
export {
  Button,
  Card,
  Chip,
  CountdownCell,
  FAQItem,
  PromoBar,
  Root,
  SectionHeader,
  Stat,
  StatStrip
};
