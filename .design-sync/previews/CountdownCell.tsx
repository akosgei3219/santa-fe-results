import React from 'react';
import { CountdownCell } from '@santa-fe-half-marathon/design-system';

/** The full race-day clock — four cells in a row. */
export const Clock = () => (
  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
    <CountdownCell value="12" label="days" />
    <CountdownCell value="06" label="hours" />
    <CountdownCell value="41" label="minutes" />
    <CountdownCell value="09" label="seconds" />
  </div>
);

/** A single unit: huge gold number over a tiny uppercase label. */
export const Single = () => <CountdownCell value="12" label="days" />;

/** Before the clock starts, the site renders em-dash placeholders. */
export const Placeholder = () => (
  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
    <CountdownCell value="—" label="days" />
    <CountdownCell value="—" label="hours" />
  </div>
);
