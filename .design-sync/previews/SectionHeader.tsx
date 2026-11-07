import React from 'react';
import { SectionHeader } from '@santa-fe-half-marathon/design-system';

/** All three slots: gold uppercase eyebrow, black-weight title, muted sub. */
export const Full = () => (
  <SectionHeader
    eyebrow="The course"
    title="Street miles, then the river trail"
    sub="Start at 6,640 ft in Agua Fria Village, dip to 6,567 ft near mile 4, climb to the 6,883 ft turnaround at mile 9, then run back down to the farm at 6,590 ft."
  />
);

/** Title only — eyebrow and sub are both optional. */
export const TitleOnly = () => <SectionHeader title="Race day" />;

/** Eyebrow + title, no sub: the compact section opener. */
export const WithEyebrow = () => (
  <SectionHeader eyebrow="The essentials" title="Everything for race weekend" />
);
