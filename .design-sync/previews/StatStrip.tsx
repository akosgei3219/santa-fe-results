import React from 'react';
import { StatStrip, Stat } from '@santa-fe-half-marathon/design-system';

/** The four race facts banded across the homepage. */
export const RaceFacts = () => (
  <StatStrip>
    <Stat value="13.109" label="USATF miles" />
    <Stat value="7:30 AM" label="Start · Eldorado" />
    <Stat value="net −36′" label="Downhill finish" />
    <Stat value="3:30" label="Course cutoff" />
  </StatStrip>
);

/** Auto-fit columns: fewer stats stretch to fill the band. */
export const TwoUp = () => (
  <StatStrip>
    <Stat value="6,992′" label="Start elevation" />
    <Stat value="6,956′" label="Finish · Railyard Park" />
  </StatStrip>
);
