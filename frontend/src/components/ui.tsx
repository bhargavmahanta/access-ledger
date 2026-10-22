import { useEffect, useRef, useId, type ReactNode } from 'react';
import { ChevronLeft, ChevronRight, X, Inbox, CircleCheck, CircleAlert } from 'lucide-react';
export const dateTime = (value: string) => new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
export function Badge({ children, good }: { children: ReactNode; good: boolean }) { return <span className={`badge ${good ? 'good' : 'muted'}`}><span aria-hidden="true" />{children}</span>; }
export function Header({ title, description, children }: { title: string; description: string; children?: ReactNode }) { return <header className="page-heading"><div><div className="eyebrow">Organization workspace</div><h1>{title}</h1><p>{description}</p></div><div>{children}</div></header>; }
export function Panel({ title, caption, children, action }: { title: string; caption?: string; children: ReactNode; action?: ReactNode }) { return <section className="panel"><div className="panel-heading"><div><h2>{title}</h2>{caption && <p>{caption}</p>}</div>{action}</div>{children}</section>; }
export function Feedback({ error, success }: { error?: string; success?: string }) { return <>{error && <div className="notice error" role="alert"><CircleAlert size={18} aria-hidden="true"/>{error}</div>}{success && <div className="notice success" role="status"><CircleCheck size={18} aria-hidden="true"/>{success}</div>}</>; }
export function Loading({ error, loading }: { error?: Error; loading?: boolean }) { return <>{error && <div className="notice error" role="alert">{error.message} <button className="text-button" onClick={() => location.reload()}>Retry</button></div>}{loading && <div className="loading-state" role="status"><span className="sr-only">Loading records…</span><div className="skeleton-line"/><div className="skeleton-line"/><div className="skeleton-line"/></div>}</>; }
export function Empty({ text = 'No records to display.' }: { text?: string }) { return <div className="empty"><Inbox size={25} aria-hidden="true"/><p>{text}</p></div>; }
export function Pager({ total, offset, limit, onChange }: { total: number; offset: number; limit: number; onChange: (n: number) => void }) { return <div className="pager"><span>{total ? `${offset+1}–${Math.min(offset+limit,total)} of ${total}` : '0 records'}</span><div><button className="icon-button" aria-label="Previous page" disabled={offset===0} onClick={() => onChange(Math.max(0,offset-limit))}><ChevronLeft size={16}/></button><button className="icon-button" aria-label="Next page" disabled={offset+limit>=total} onClick={() => onChange(offset+limit)}><ChevronRight size={16}/></button></div></div>; }
export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog?.showModal();
    // React autofocus runs before a native dialog becomes visible.
    dialog?.querySelector<HTMLElement>('input:not([disabled]), select:not([disabled]), textarea:not([disabled])')?.focus();
    return () => { dialog?.close(); if (previousFocus?.isConnected) previousFocus.focus(); };
  }, []);
  return <dialog ref={ref} aria-labelledby={titleId} onCancel={onClose}><div className="modal-heading"><h2 id={titleId}>{title}</h2><button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20}/></button></div>{children}</dialog>;
}
export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) { const id=useId(); return <div className="field"><label htmlFor={id}>{label}</label><select id={id} {...props}><option value="">Select…</option>{children}</select></div>; }
