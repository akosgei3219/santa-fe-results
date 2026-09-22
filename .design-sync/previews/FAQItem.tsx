import React from 'react';
import { FAQItem } from '@santa-fe-half-marathon/design-system';

/** Collapsed — the default. The gold "+" is the affordance. */
export const Collapsed = () => (
  <FAQItem question="Is there a time limit?">
    Yes — 3 hours 30 minutes.
  </FAQItem>
);

/** `defaultOpen` expands the answer; the indicator flips to a dash. */
export const Open = () => (
  <FAQItem question="How long is the course, really?" defaultOpen>
    13.109 miles, USATF-certified, and net-downhill: you start at 6,992 ft, top
    out at 7,330 ft near mile 4, and finish at 6,956 ft in Railyard Park.
  </FAQItem>
);

/** Stacked items share hairline dividers — how the FAQ section is built. */
export const List = () => (
  <div>
    <FAQItem question="Where do I pick up my packet?" defaultOpen>
      At the expo at Old Warehouse 21, next to Railyard Park: Friday 12–6 PM and
      Saturday 10 AM–5 PM.
    </FAQItem>
    <FAQItem question="How do I register?">
      On RunSignup — registration is open now.
    </FAQItem>
    <FAQItem question="Will there be race photos?">
      Yes, free ones — from the start line in Eldorado to the Railyard finish.
    </FAQItem>
  </div>
);
