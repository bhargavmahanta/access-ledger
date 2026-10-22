import { useState } from 'react';
import useSWR, { mutate } from 'swr';
import type { Page } from './types';
const prefix = '/api/v1';
export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const r = await fetch(prefix + path, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) {
    let message = `Request failed (${r.status}).`;
    try { const data = await r.json(); message = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((e: {msg: string}) => e.msg).join('; ') : data.reason_code?.replaceAll('_', ' ') || message; } catch { /* Keep the HTTP error when the response is not JSON. */ }
    throw new Error(message);
  }
  return r.status === 204 ? undefined as T : r.json();
}
export function useData<T>(path: string|null) { return useSWR<T>(path, request, { revalidateOnFocus: false, shouldRetryOnError: false }); }
export function useAll<T>(path: string|null) {
  return useSWR<T[]>(path ? ['all', path] : null, async ([, url]: string[]) => {
    const first = await request<Page<T>>(url+'?limit=200');
    const rest = await Promise.all(Array.from({ length: Math.ceil(first.total/200)-1 }, (_, i) => request<Page<T>>(`${url}?limit=200&offset=${(i+1)*200}`)));
    return [...first.items, ...rest.flatMap(p => p.items)];
  }, { revalidateOnFocus: false, shouldRetryOnError: false });
}
export function useAction() {
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [success, setSuccess] = useState('');
  async function run(work: () => Promise<unknown>, message: string) {
    setBusy(true); setError(''); setSuccess('');
    try { await work(); await mutate(() => true, undefined, { revalidate: true }); setSuccess(message); return true; }
    catch (e) { setError(e instanceof Error ? e.message : 'Operation failed. Try again.'); return false; }
    finally { setBusy(false); }
  }
  return { busy, error, success, run };
}
