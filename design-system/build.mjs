import { build } from 'esbuild';
import { copyFileSync, mkdirSync, writeFileSync } from 'node:fs';

mkdirSync('dist', { recursive: true });

const shared = {
  entryPoints: ['src/index.jsx'],
  bundle: true,
  external: ['react', 'react-dom'],
  jsx: 'automatic',
  target: 'es2019',
  logLevel: 'warning',
};

await build({ ...shared, format: 'esm', outfile: 'dist/index.mjs' });
await build({ ...shared, format: 'cjs', outfile: 'dist/index.js' });
copyFileSync('src/styles.css', 'dist/styles.css');

// Hand-maintained types matching src/index.jsx exactly.
writeFileSync('dist/index.d.ts', `import * as React from 'react';

export interface RootProps extends React.HTMLAttributes<HTMLDivElement> { children?: React.ReactNode; }
export declare function Root(props: RootProps): JSX.Element;

export interface ButtonProps extends React.HTMLAttributes<HTMLElement> {
  /** "solid" = gold fill (default); "ghost" = outline on dark. */
  variant?: 'solid' | 'ghost';
  /** When set, renders an <a> instead of a <button>. */
  href?: string;
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): JSX.Element;

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Adds the standard 24px inset. */
  padded?: boolean;
  children?: React.ReactNode;
}
export declare function Card(props: CardProps): JSX.Element;

export interface SectionHeaderProps extends React.HTMLAttributes<HTMLElement> {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  sub?: React.ReactNode;
}
export declare function SectionHeader(props: SectionHeaderProps): JSX.Element;

export interface StatProps extends React.HTMLAttributes<HTMLDivElement> {
  value: React.ReactNode;
  label: React.ReactNode;
}
export declare function Stat(props: StatProps): JSX.Element;

export interface StatStripProps extends React.HTMLAttributes<HTMLDivElement> { children?: React.ReactNode; }
export declare function StatStrip(props: StatStripProps): JSX.Element;

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  title: React.ReactNode;
  detail?: React.ReactNode;
}
export declare function Chip(props: ChipProps): JSX.Element;

export interface CountdownCellProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: React.ReactNode;
  label: React.ReactNode;
}
export declare function CountdownCell(props: CountdownCellProps): JSX.Element;

export interface FAQItemProps extends React.HTMLAttributes<HTMLElement> {
  question: React.ReactNode;
  defaultOpen?: boolean;
  children?: React.ReactNode;
}
export declare function FAQItem(props: FAQItemProps): JSX.Element;

export interface PromoBarProps extends React.HTMLAttributes<HTMLDivElement> { children?: React.ReactNode; }
export declare function PromoBar(props: PromoBarProps): JSX.Element;
`);

console.log('built dist/: index.mjs, index.js, index.d.ts, styles.css');
