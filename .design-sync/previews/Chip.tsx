import React from 'react';
import { Chip } from '@santa-fe-half-marathon/design-system';

/** Bold title line over a muted detail line, in a bordered pill. */
export const Single = () => <Chip title="13.1" detail="GPS miles" />;

/** `detail` is optional — title alone still reads as a chip. */
export const TitleOnly = () => <Chip title="Bib pickup opens Friday" />;

/** The course-facts row from the site: chips wrap as the container narrows. */
export const CourseRow = () => (
  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
    <Chip title="13.1" detail="GPS miles" />
    <Chip title="6,883′" detail="High · mile 9" />
    <Chip title="6,590′" detail="Finish" />
    <Chip title="+651′" detail="Total climb" />
  </div>
);
