import React from 'react';
import { Stat, StatStrip } from '@santa-fe-half-marathon/design-system';

/** One fact: gold tabular value over a muted uppercase label. */
export const Distance = () => <Stat value="13.109" label="USATF miles" />;

/** Values are free-form nodes — times, elevations and deltas all fit. */
export const Cutoff = () => <Stat value="3:30" label="Course cutoff" />;

/** In its natural home: Stat is the child StatStrip bands and divides. */
export const InsideStrip = () => (
  <StatStrip>
    <Stat value="7:30 AM" label="Start · Eldorado" />
    <Stat value="net −36′" label="Downhill finish" />
  </StatStrip>
);
