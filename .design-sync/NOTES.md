# design-sync notes — @santa-fe-half-marathon/design-system

## Layout

- The design system is the `design-system/` subpackage (npm + esbuild). The repo
  root is a Python project — don't run node tooling from it expecting a package.
- No Storybook anywhere in the repo, so `shape: "package"`. The component list
  comes from the shipped `dist/index.d.ts` exports: 10 components.
- `dist/index.d.ts` is **hand-maintained inside `design-system/build.mjs`** (the
  build script writes it as a string; it is not generated from source). If props
  change in `src/index.jsx`, that string must be updated by hand or the synced
  `.d.ts` contract silently lies to the design agent.

## Build recipe (exact, from the repo root)

```sh
cd design-system && npm ci && npm run build && cd ..
cp -r .ds-sync/node_modules/@types design-system/node_modules/   # see @types note
node .ds-sync/resync.mjs --config .design-sync/config.json \
  --node-modules ./design-system/node_modules \
  --entry ./design-system/dist/index.mjs --out ./ds-bundle
```

## Gotchas that cost time — don't rediscover these

- **`@types/react` is not a dependency of `design-system/`.** Without it in
  `--node-modules` the converter prints `[DTS_REACT]` and every prop inherited
  from `React.HTMLAttributes<…>` resolves to `any`, gutting the `.d.ts`
  contracts. Fix: copy it in from the staged converter deps (line above).
  **`npm ci` wipes this — re-do it after every install.**
- **All 10 components live in one file, `src/index.jsx`.** The converter's fuzzy
  src-matcher expects `<Name>.tsx` / `<Name>/index.tsx` and matched 0 of 10,
  which drops the JSDoc from every `.prompt.md`. Fix: `componentSrcMap` pins all
  ten names to `src/index.jsx` (already in config.json). **Add a map entry for
  any new component**, or it ships without its doc line.
- **`cfg.provider = {component: "Root"}` is required.** `Root` applies
  `.sfhm-root`, which carries the obsidian background, brand font stack and
  line-height. Without the provider every preview renders black-on-white browser
  default and grades unstyled.
- **Playwright must match the cached chromium build.** This sandbox ships
  chromium **1194** at `/opt/pw-browsers`; only **playwright@1.56.0** pins that
  revision. Latest (1.63) pins 1243 and dies with
  `browserType.launch: Executable doesn't exist`. Verify against
  `node_modules/playwright-core/browsers.json` before installing.
- **No `[FONT_MISSING]`, and that is correct.** `.sfhm-root` uses a system font
  stack by design; there is no brand webfont to ship. Don't go hunting for one.

## Preview sources

`design-system/src/styles.css` states the tokens and component styles were
lifted verbatim from `site/index.html`. That file is therefore the real
composition source — all 10 authored previews in `.design-sync/previews/` use
copy and numbers taken from it (distance, elevations, cutoff, expo hours, promo
code), not invented content. When re-authoring, go back to `site/index.html`.

## Known render warns

None. The last full run exited clean with zero warnings — 10/10 previews render,
no floor cards, no `[RENDER_THIN]`, no `[GRID_OVERFLOW]`. **Any warn on a future
run is new** — investigate it rather than assuming it was always there.

## Upload state

**Never uploaded.** There is no `projectId` in config.json and no remote
`_ds_sync.json` anchor, so the next sync is a full first sync, not a re-sync.

DesignSync authorization does **not** work in remote claude.ai/code sessions —
confirmed again 2026-09-22; the tool returns "DesignSync needs design-system
authorization, and /design-login cannot run in this non-interactive session."
To upload, either run `/design-login` once from an interactive Claude Code
session on a local machine, or use Claude Design's "Send to Claude Code Web".
Everything else — build, validation, previews, grades, conventions header — is
done and committed; an authorized session should only need to create the
project and push `ds-bundle/`.

## Re-sync risks — what can go stale silently

- **The `@types/react` copy and `.ds-sync/` are gitignored**, so a fresh clone
  has neither. Both steps in the build recipe must be re-run, or the run quietly
  produces weaker `.d.ts` files.
- **Preview copy is pinned to the 2026 race.** The previews hardcode the
  Sept 20 2026 date, Eldorado/Railyard elevations, the 3:30 cutoff, expo hours
  and the promo code `RUNSANTAFE26`. None of it updates itself. Diff the
  previews against `site/index.html` each year, or the design agent will imitate
  a stale race.
- **Everything is in one group, `general`.** No docs directory exists, so no
  `category` frontmatter sets groups. If per-component docs are added later the
  groups will change and the old `components/general/**` paths must land in the
  upload plan's `deletePaths`, or the project keeps orphaned duplicates.
- **The playwright pin tracks the sandbox image, not the repo.** If the image's
  chromium build changes, 1.56.0 becomes the wrong version — re-derive it rather
  than trusting this note.
- **`dist/` is committed to the repo** but the build regenerates it. If a sync
  ever reports components that don't match `src/index.jsx`, suspect a stale
  committed `dist/` and rebuild before diagnosing further.
- **`conventions.md` enumerates real class and token names.** It was validated
  against the build on 2026-09-22 (15 classes, 9 tokens with exact hex values,
  10 components, all props). If `styles.css` changes, re-run that validation —
  a conventions file naming things that no longer exist is worse than none.
