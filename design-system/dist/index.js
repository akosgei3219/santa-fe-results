var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.jsx
var index_exports = {};
__export(index_exports, {
  Button: () => Button,
  Card: () => Card,
  Chip: () => Chip,
  CountdownCell: () => CountdownCell,
  FAQItem: () => FAQItem,
  PromoBar: () => PromoBar,
  Root: () => Root,
  SectionHeader: () => SectionHeader,
  Stat: () => Stat,
  StatStrip: () => StatStrip
});
module.exports = __toCommonJS(index_exports);
var import_react = __toESM(require("react"));
var import_jsx_runtime = require("react/jsx-runtime");
function Root({ children, style, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sfhm-root", style, ...rest, children });
}
function Button({ variant = "solid", href, children, className = "", ...rest }) {
  const cls = `sfhm-btn${variant === "ghost" ? " sfhm-btn--ghost" : ""} ${className}`.trim();
  if (href) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", { className: cls, href, ...rest, children });
  }
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "button", className: cls, ...rest, children });
}
function Card({ padded = false, children, className = "", ...rest }) {
  const cls = `sfhm-card${padded ? " sfhm-card--padded" : ""} ${className}`.trim();
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: cls, ...rest, children });
}
function SectionHeader({ eyebrow, title, sub, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", { ...rest, children: [
    eyebrow && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "sfhm-eyebrow", children: eyebrow }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { className: "sfhm-section-title", children: title }),
    sub && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "sfhm-section-sub", children: sub })
  ] });
}
function Stat({ value, label, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "sfhm-stat", ...rest, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: value }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: label })
  ] });
}
function StatStrip({ children, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sfhm-stat-strip", ...rest, children });
}
function Chip({ title, detail, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "sfhm-chip", ...rest, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: title }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: detail })
  ] });
}
function CountdownCell({ value, label, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "sfhm-count-cell", ...rest, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: value }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: label })
  ] });
}
function FAQItem({ question, defaultOpen = false, children, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("details", { className: "sfhm-faq-item", open: defaultOpen || void 0, ...rest, children: [
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("summary", { children: question }),
    /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sfhm-faq-answer", children })
  ] });
}
function PromoBar({ children, ...rest }) {
  return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sfhm-promo-bar", ...rest, children });
}
