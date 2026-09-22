import React from 'react';
import {
  Root, PromoBar, SectionHeader, StatStrip, Stat, Button,
} from '@santa-fe-half-marathon/design-system';

/**
 * Root is the ground every page sits on: obsidian background, brand font
 * stack, and the scope the --sfhm-* tokens resolve against.
 */
export const PageGround = () => (
  <Root style={{ padding: 28 }}>
    <SectionHeader
      eyebrow="Sunday · September 20, 2026 · 7:30 AM"
      title="Santa Fe International Half Marathon"
      sub="Point-to-point and net-downhill, from Eldorado to Railyard Park."
    />
    <Button>Register on RunSignup</Button>
  </Root>
);

/** A full section assembled on the Root ground — the normal page shape. */
export const WithSections = () => (
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
);
