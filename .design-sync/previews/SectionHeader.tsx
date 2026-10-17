import React from 'react';
import { SectionHeader } from '@santa-fe-half-marathon/design-system';

/** All three slots: gold uppercase eyebrow, black-weight title, muted sub. */
export const Full = () => (
  <SectionHeader
    eyebrow="The course"
    title="Point-to-point, net downhill"
    sub="Start at 6,992 ft in Eldorado, climb to the 7,330 ft high point near mile 4, then descend to the Railyard Park finish."
  />
);

/** Title only — eyebrow and sub are both optional. */
export const TitleOnly = () => <SectionHeader title="Race day" />;

/** Eyebrow + title, no sub: the compact section opener. */
export const WithEyebrow = () => (
  <SectionHeader eyebrow="The essentials" title="Everything for race weekend" />
);
