import { useEffect, useState } from 'react';
import { getPricing } from './api';
import type { Pricing } from './types/api';
export { nitroUsdCents, tomanCents } from './pricingValues';
import { DEFAULT_PRICING } from './pricingValues';

let cachedPricing: Pricing | null = null;

export const usePricing = () => {
  const [pricing, setPricing] = useState(cachedPricing ?? DEFAULT_PRICING);
  const [pricingLoading, setPricingLoading] = useState(cachedPricing === null);
  const [pricingError, setPricingError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (cachedPricing) {
      return;
    }
    getPricing()
      .then(value => {
        cachedPricing = value;
        if (!cancelled) setPricing(value);
      })
      .catch(() => {
        if (!cancelled) setPricingError(true);
      })
      .finally(() => {
        if (!cancelled) setPricingLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { pricing, pricingLoading, pricingError };
};
