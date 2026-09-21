import React from 'react';

/** Root wrapper: obsidian ground, brand font stack, and the token scope. */
export function Root({ children, style, ...rest }) {
  return (
    <div className="sfhm-root" style={style} {...rest}>
      {children}
    </div>
  );
}

/** Brand button. variant: "solid" (gold, default) | "ghost" (outline). Renders <a> when href is given. */
export function Button({ variant = 'solid', href, children, className = '', ...rest }) {
  const cls = `sfhm-btn${variant === 'ghost' ? ' sfhm-btn--ghost' : ''} ${className}`.trim();
  if (href) {
    return <a className={cls} href={href} {...rest}>{children}</a>;
  }
  return <button type="button" className={cls} {...rest}>{children}</button>;
}

/** Rounded obsidian card. padded adds the standard 24px inset. */
export function Card({ padded = false, children, className = '', ...rest }) {
  const cls = `sfhm-card${padded ? ' sfhm-card--padded' : ''} ${className}`.trim();
  return <div className={cls} {...rest}>{children}</div>;
}

/** Section opener: gold uppercase eyebrow, black-weight title, muted sub. */
export function SectionHeader({ eyebrow, title, sub, ...rest }) {
  return (
    <header {...rest}>
      {eyebrow && <p className="sfhm-eyebrow">{eyebrow}</p>}
      <h2 className="sfhm-section-title">{title}</h2>
      {sub && <p className="sfhm-section-sub">{sub}</p>}
    </header>
  );
}

/** One big-number fact: gold tabular value over a muted uppercase label. */
export function Stat({ value, label, ...rest }) {
  return (
    <div className="sfhm-stat" {...rest}>
      <b>{value}</b>
      <span>{label}</span>
    </div>
  );
}

/** Full-width band of Stats, divided by hairlines. Children should be <Stat>. */
export function StatStrip({ children, ...rest }) {
  return <div className="sfhm-stat-strip" {...rest}>{children}</div>;
}

/** Small labeled chip: bold title line, muted detail line. */
export function Chip({ title, detail, ...rest }) {
  return (
    <span className="sfhm-chip" {...rest}>
      <b>{title}</b>
      <span>{detail}</span>
    </span>
  );
}

/** One countdown unit: huge gold number over a tiny uppercase label. */
export function CountdownCell({ value, label, ...rest }) {
  return (
    <span className="sfhm-count-cell" {...rest}>
      <b>{value}</b>
      <span>{label}</span>
    </span>
  );
}

/** Accordion Q&A row (native details/summary; gold +/– indicator). */
export function FAQItem({ question, defaultOpen = false, children, ...rest }) {
  return (
    <details className="sfhm-faq-item" open={defaultOpen || undefined} {...rest}>
      <summary>{question}</summary>
      <div className="sfhm-faq-answer">{children}</div>
    </details>
  );
}

/** Gold announcement band. Use <code> inside for promo codes. */
export function PromoBar({ children, ...rest }) {
  return <div className="sfhm-promo-bar" {...rest}>{children}</div>;
}
