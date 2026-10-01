import React from 'react';
import { PromoBar } from '@santa-fe-half-marathon/design-system';

/** The lodging promo from the site — <code> styles the promo code. */
export const Lodging = () => (
  <PromoBar>
    Race-week lodging: save 15% at the Pecos Trail Inn with code{' '}
    <code>RUNSANTAFE26</code>
  </PromoBar>
);

/** Links invert to obsidian on the gold band. */
export const WithLink = () => (
  <PromoBar>
    Registration is open — <a href="https://runsignup.com">sign up on RunSignup</a>
  </PromoBar>
);

/** Plain announcement, no code or link. */
export const Plain = () => (
  <PromoBar>Expo opens Friday at noon — Old Warehouse 21.</PromoBar>
);
