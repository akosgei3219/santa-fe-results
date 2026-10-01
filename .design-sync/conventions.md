## Building with this design system

Ten React components lifted from the race's own site. Every export lands on
`window.SFHM` — destructure from there.

### Always wrap the tree in `Root`

`Root` is not decoration. It applies `.sfhm-root`, which carries the obsidian
background, the brand font stack, and the line-height everything else inherits.
Render a component outside `Root` and you get browser defaults on a white page:
the `--sfhm-*` tokens still resolve (they sit on `:root`), but nothing reads as
the race. There is no theme prop and no second provider — `Root` is the whole
setup.

```jsx
const { Root, SectionHeader, Button } = window.SFHM;

<Root style={{ padding: 28 }}>
  <SectionHeader eyebrow="The essentials" title="Race weekend" />
  <Button>Register on RunSignup</Button>
</Root>
```

There is no brand webfont. `.sfhm-root` sets a system stack
(`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, …`) — don't go looking
for font files to load.

### The idiom: components own their classes, you style with tokens

Each component applies its own `sfhm-*` class. Don't hand-write those classes
and never reimplement their rules — reach for props instead (`variant`,
`padded`, `defaultOpen`). `Button` and `Card` merge an extra `className` when
you genuinely need a hook.

For your own glue — page chrome, grids, spacing — use the custom properties.
They are the design language:

| Token | Value | Use for |
|---|---|---|
| `--sfhm-bg` | `#0A0A0A` | page ground |
| `--sfhm-card-bg` | `#121212` | raised surfaces |
| `--sfhm-row` | `#161616` | alternating rows |
| `--sfhm-border` | `#1E1E1E` | hairlines, dividers |
| `--sfhm-text` | `#ffffff` | primary text |
| `--sfhm-text-muted` | `#A3A3A3` | labels, secondary copy |
| `--sfhm-gold` | `#FFB800` | the accent — numbers, eyebrows, CTAs |
| `--sfhm-crimson` | `#D6221D` | accent |
| `--sfhm-turquoise` | `#00A896` | accent |

`--sfhm-row`, `--sfhm-crimson` and `--sfhm-turquoise` are defined but unused by
the components — they're yours for app-level chrome.

Gold carries emphasis and nothing else. Big numbers, eyebrows, and the primary
button are gold; body copy is `--sfhm-text`, supporting copy
`--sfhm-text-muted`. A page where everything is gold is wrong.

Classes the components apply, if you need to recognize them in the DOM:
`.sfhm-root`, `.sfhm-btn`, `.sfhm-btn--ghost`, `.sfhm-card`,
`.sfhm-card--padded`, `.sfhm-eyebrow`, `.sfhm-section-title`,
`.sfhm-section-sub`, `.sfhm-stat`, `.sfhm-stat-strip`, `.sfhm-chip`,
`.sfhm-count-cell`, `.sfhm-faq-item`, `.sfhm-faq-answer`, `.sfhm-promo-bar`.

### Composition rules worth knowing

- `Stat` belongs inside `StatStrip` — the strip draws the band and the hairline
  dividers between cells. A bare `Stat` renders, but loses both.
- `PromoBar` expects `<code>` for promo codes and `<a>` for links; both are
  styled to invert on the gold band.
- `FAQItem` is a native `<details>`. Stack siblings directly — they share the
  bottom hairline. `defaultOpen` is the only open-state control.
- `CountdownCell`, `Chip` and `Stat` all take short `value`/`title` + label
  pairs. Keep values terse (`13.109`, `7:30 AM`, `net −36′`) — the type is
  tabular and sized for glanceable facts.

### Where the truth lives

Read `_ds/<folder>/styles.css` before styling; it `@import`s `_ds_bundle.css`,
which holds the `:root` token block and every component rule. Per component,
`<Name>.d.ts` is the prop contract and `<Name>.prompt.md` the usage note.

### An idiomatic section

```jsx
const { Root, PromoBar, SectionHeader, StatStrip, Stat } = window.SFHM;

<Root>
  <PromoBar>
    Race-week lodging: save 15% with code <code>RUNSANTAFE26</code>
  </PromoBar>
  <div style={{ padding: 28 }}>
    <SectionHeader eyebrow="The essentials" title="Race weekend" />
  </div>
  <StatStrip>
    <Stat value="13.109" label="USATF miles" />
    <Stat value="7:30 AM" label="Start · Eldorado" />
    <Stat value="3:30" label="Course cutoff" />
  </StatStrip>
</Root>
```
