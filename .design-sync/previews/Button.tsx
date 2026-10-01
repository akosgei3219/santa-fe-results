import React from 'react';
import { Button } from '@santa-fe-half-marathon/design-system';

/** Gold fill — the primary race CTA. */
export const Solid = () => <Button>Register on RunSignup</Button>;

/** Outline on obsidian — the secondary action beside a solid CTA. */
export const Ghost = () => <Button variant="ghost">See the course</Button>;

/** With `href` the button renders an <a>, keeping identical styling. */
export const AsLink = () => (
  <Button href="https://runsignup.com">View Live Leaderboard →</Button>
);

/** The pairing used across the site: one solid CTA, one ghost alternative. */
export const Pair = () => (
  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
    <Button>Register on RunSignup</Button>
    <Button variant="ghost">See the course</Button>
  </div>
);
