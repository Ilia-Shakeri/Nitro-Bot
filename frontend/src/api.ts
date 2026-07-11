import WebApp from '@twa-dev/sdk';
import type { User, Transaction, Release, LedgerEntry, SupportTicket } from './types/api';

const isDev = import.meta.env.MODE === 'development';
const BASE   = import.meta.env.VITE_API_URL || (isDev ? 'http://localhost:8000' : '');

/**
 * Resolve the signed Telegram initData string used to authenticate the user.
 * Order of preference:
 *   1. WebApp.initData from the SDK (already a signed query string).
 *   2. window.Telegram.WebApp.initData — covers cases where the SDK singleton
 *      is initialised before Telegram injects the global (StrictMode re-mounts).
 *   3. Rebuild a query string from initDataUnsafe as a last resort. This is NOT
 *      signed, so it only authenticates when the backend runs with
 *      SKIP_TELEGRAM_AUTH=true (local dev); in production it fails closed.
 */
const getInitData = (): string => {
  if (WebApp.initData) return WebApp.initData;

  const tg = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
  if (tg?.initData) return tg.initData;

  const unsafe = WebApp.initDataUnsafe as unknown as Record<string, unknown> | undefined;
  if (unsafe && Object.keys(unsafe).length > 0) {
    return Object.entries(unsafe)
      .map(([k, v]) => `${k}=${encodeURIComponent(typeof v === 'object' ? JSON.stringify(v) : String(v))}`)
      .join('&');
  }
  return '';
};

const authHeaders = (): HeadersInit => ({
  'X-Telegram-Init-Data': getInitData(),
});

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const getUser = () =>
  request<User>('/users/me');

export const updateLanguage = (lang: string) =>
  request<{ status: string; language: string }>('/users/me/language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: lang }),
  });

export const getTransactions = () =>
  request<Transaction[]>('/users/me/transactions').catch((): Transaction[] => []);

export const getLedger = () =>
  request<LedgerEntry[]>('/transactions/ledger').catch((): LedgerEntry[] => []);

export const getReleases = () =>
  request<Release[]>('/users/me/releases').catch((): Release[] => []);

export const submitRelease = (formData: FormData) =>
  request<{ status: string; release_id: number; credits_left: number; cost_deducted: number }>(
    '/releases',
    { method: 'POST', body: formData },
  );

export const submitTicket = (subject: string, message: string) =>
  request<{ status: string }>('/support/tickets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject, message }),
  });

export const getTickets = () =>
  request<SupportTicket[]>('/support/tickets').catch((): SupportTicket[] => []);

export const getUsdtRate = () =>
  request<{ rate_toman: number; cached: boolean }>('/transactions/usdt-rate');

export const submitReceipt = (file: File | null, amount: number, paymentMethod: string) => {
  const form = new FormData();
  form.append('amount', amount.toString());
  form.append('payment_method', paymentMethod);
  if (file) form.append('receipt', file);
  return request<{ status: string; transaction_id: number }>('/transactions/receipt', {
    method: 'POST',
    body: form,
  });
};
