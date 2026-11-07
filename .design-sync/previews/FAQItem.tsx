import React from 'react';
import { FAQItem } from '@santa-fe-half-marathon/design-system';

/** Collapsed — the default. The gold "+" is the affordance. */
export const Collapsed = () => (
  <FAQItem question="Is there a time limit?">
    Yes — 4 hours 30 minutes.
  </FAQItem>
);

/** `defaultOpen` expands the answer; the indicator flips to a dash. */
export const Open = () => (
  <FAQItem question="How long is the course, really?" defaultOpen>
    13.1 GPS-measured miles: you start at 6,640 ft in Agua Fria Village, dip to
    6,567 ft near mile 4, climb to the 6,883 ft turnaround at mile 9, and finish
    at 6,590 ft — about 651 ft of total climb.
  </FAQItem>
);

/** Stacked items share hairline dividers — how the FAQ section is built. */
export const List = () => (
  <div>
    <FAQItem question="Where do I pick up my packet?" defaultOpen>
      At Reunity Resources Farm, for all events: Friday 10 AM–6 PM and Saturday
      10 AM–5 PM. 5K and 10K bibs are mailed about a week ahead.
    </FAQItem>
    <FAQItem question="How do I register?">
      On RunSignup — registration is open now.
    </FAQItem>
    <FAQItem question="Will there be race photos?">
      Yes, free ones — every year. Links to all the galleries are in the Photos
      section.
    </FAQItem>
  </div>
);
