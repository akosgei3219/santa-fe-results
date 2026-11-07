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
      eyebrow="Sunday · September 19, 2027 · 7:30 AM"
      title="Santa Fe International Half Marathon"
      sub="Street miles out of Agua Fria Village, then the car-free river trail to a farm finish at Reunity Resources."
    />
    <Button>Register on RunSignup</Button>
  </Root>
);

/** A full section assembled on the Root ground — the normal page shape. */
export const WithSections = () => (
  <Root>
    <PromoBar>
      Registration is open —{' '}
      <a href="https://runsignup.com/Race/Register/?raceId=89412">
        sign up on RunSignup
      </a>
    </PromoBar>
    <div style={{ padding: 28 }}>
      <SectionHeader eyebrow="The essentials" title="Race weekend" />
    </div>
    <StatStrip>
      <Stat value="13.1" label="GPS-measured miles" />
      <Stat value="7:30 AM" label="Start · Agua Fria" />
      <Stat value="4:30" label="Course cutoff" />
    </StatStrip>
  </Root>
);
