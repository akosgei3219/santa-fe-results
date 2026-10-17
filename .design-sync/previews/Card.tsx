import React from 'react';
import { Card, SectionHeader, Chip } from '@santa-fe-half-marathon/design-system';

/** `padded` adds the standard 24px inset — the common case. */
export const Padded = () => (
  <Card padded>
    <SectionHeader
      eyebrow="Race weekend"
      title="Packet pickup"
      sub="Old Warehouse 21, next to Railyard Park. Friday 12–6 PM, Saturday 10 AM–5 PM."
    />
  </Card>
);

/** Flush (default): no inset, for edge-to-edge content. */
export const Flush = () => (
  <Card>
    <div style={{ padding: '14px 18px' }}>
      Flush card — content controls its own inset.
    </div>
  </Card>
);

/** Cards hold whatever the section needs; here a row of course chips. */
export const WithChips = () => (
  <Card padded>
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
      <Chip title="13.109" detail="USATF miles" />
      <Chip title="7,330′" detail="High · mile 4" />
      <Chip title="6,956′" detail="Finish" />
    </div>
  </Card>
);
