import React from 'react';
import { StatStrip, Stat } from '@santa-fe-half-marathon/design-system';

/** The four race facts banded across the homepage. */
export const RaceFacts = () => (
  <StatStrip>
    <Stat value="13.1" label="GPS-measured miles" />
    <Stat value="7:30 AM" label="Start · Agua Fria" />
    <Stat value="+651′" label="Total climb" />
    <Stat value="4:30" label="Course cutoff" />
  </StatStrip>
);

/** Auto-fit columns: fewer stats stretch to fill the band. */
export const TwoUp = () => (
  <StatStrip>
    <Stat value="6,640′" label="Start elevation" />
    <Stat value="6,590′" label="Finish · Reunity Resources" />
  </StatStrip>
);
