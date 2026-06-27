import WebApp from '@twa-dev/sdk';
import type { User, Transaction, Release } from './types/api';

const isDev = import.meta.env.MODE === 'development';
const BASE   = import.meta.env.VITE_API_URL || (isDev ? 'http://localhost:8000' : '');

const authHeaders = (): HeadersInit => ({
  'X-Telegram-Init-Data': WebApp.initData || '',
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

export const getReleases = () =>
  request<Release[]>('/users/me/releases').catch((): Release[] => []);

export const submitRelease = (formData: FormData) =>
  request<{ status: string; release_id: number; credits_left: number; cost_deducted: number }>(
    '/releases',
    { method: 'POST', body: formData },
  );

export const submitReceipt = (file: File, amount: number, paymentMethod: string) => {
  const form = new FormData();
  form.append('amount', amount.toString());
  form.append('payment_method', paymentMethod);
  form.append('receipt', file);
  return request<{ status: string; transaction_id: number }>('/transactions/receipt', {
    method: 'POST',
    body: form,
  });
};
