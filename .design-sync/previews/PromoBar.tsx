import React from 'react';
import { PromoBar } from '@santa-fe-half-marathon/design-system';

/** Plain announcement, no code or link — the band's usual job. */
export const Plain = () => (
  <PromoBar>
    Saturday’s 5K, 10K and Kids Fun Dash — start times announced soon.
  </PromoBar>
);

/** Links invert to obsidian on the gold band. */
export const WithLink = () => (
  <PromoBar>
    Registration is open —{' '}
    <a href="https://runsignup.com/Race/Register/?raceId=89412">
      sign up on RunSignup
    </a>
  </PromoBar>
);

/**
 * `<code>` is styled to invert on the band, for a promo code. There is no 2027
 * promo (the 2026 lodging offer expired and the site's promo bar came down with
 * it), so the code below is a placeholder showing the styling — not a real
 * offer. Swap in the season's actual code if one is announced.
 */
export const WithCode = () => (
  <PromoBar>
    Race-week lodging: save 15% with code <code>PROMOCODE</code>
  </PromoBar>
);
