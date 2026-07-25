import type { Pricing } from './types/api';

export const DEFAULT_PRICING: Pricing = {
  nitro_usd_price_cents: 80,
  original_release_price: 20,
  discounted_release_price: 8,
  copyright_price: 2,
  edit_release_price: 2,
  minimum_topup_nitro: 3,
};

export const nitroUsdCents = (quantity: number, pricing: Pricing) =>
  quantity * pricing.nitro_usd_price_cents;

export const tomanCents = (quantity: number, rate: number, pricing: Pricing) =>
  nitroUsdCents(quantity, pricing) * rate;
