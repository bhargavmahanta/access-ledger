import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { BookOpenCheck, LayoutDashboard, Users, KeyRound, Database, ScanLine, ListFilter, Menu, ArrowRight, Search, X, Command } from 'lucide-react';
import { Empty, Modal } from './components/ui';
const nav = [ ['/', 'Dashboard', LayoutDashboard], ['/users', 'Users', Users], ['/roles', 'Roles & permissions', KeyRound], ['/resources', 'Resources', Database], ['/access', 'Access evaluation', ScanLine], ['/audit', 'Audit explorer', ListFilter] ] as const;
export default function App() {
  const [open, setOpen] = useState(false);
  const [finder, setFinder] = useState(false);
  const [query, setQuery] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const current = nav.find(([path]) => path === location.pathname)?.[1] ?? 'Workspace';
  const matches = nav.filter(([, label]) => label.toLowerCase().includes(query.toLowerCase().trim()));
  function openFinder() { setQuery(''); setFinder(true); }
  function go(path: string) { setFinder(false); setOpen(false); navigate(path); }
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k' && !document.querySelector('dialog[open]')) {
        e.preventDefault(); setQuery(''); setFinder(true);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, []);
  useEffect(() => { document.title = `${current} · AccessLedger`; }, [current]);
  return <div className="app"><a className="skip-link" href="#main">Skip to content</a><button className="mobile-menu icon-button" aria-label="Open navigation" aria-expanded={open} onClick={() => setOpen(true)}><Menu/></button>{open && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setOpen(false)}/>}
    <aside className={open ? 'sidebar open' : 'sidebar'}><NavLink className="brand" to="/" onClick={() => setOpen(false)}><div className="brand-mark"><BookOpenCheck size={24}/></div><div>AccessLedger<small>Access & accountability</small></div></NavLink><button className="mobile-close icon-button" aria-label="Close navigation" onClick={() => setOpen(false)}><X/></button>
      <div className="workspace-card"><span className="workspace-avatar">AL</span><div>Organization<small>Local demonstration</small></div></div>
      <div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{nav.map(([path,label,Icon]) => <NavLink key={path} to={path} end={path==='/'} onClick={() => setOpen(false)}><Icon size={19} strokeWidth={1.7}/><span>{label}</span>{path===location.pathname && <span className="active-marker"/>}</NavLink>)}</nav>
      <div className="sidebar-footer"><BookOpenCheck size={19}/><strong>Decisions you can trace</strong><p>Manage access. Test a request.<br/>Follow the record.</p><span className="local-environment"><span className="local-dot"/>Local workspace</span></div></aside>
    <div className="workspace"><div className="topbar"><span className="breadcrumbs">Workspace <span className="slash">/</span> <strong>{current}</strong></span><button className="page-search" onClick={openFinder} aria-label="Find a page"><Search size={16}/><span>Find a page…</span><kbd><Command size={11}/> / Ctrl K</kbd></button></div><main id="main"><Outlet/></main><footer className="page-footer">AccessLedger <span>Academic demonstration · Times shown in your local timezone</span></footer></div>
    {finder && <Modal title="Find a page" onClose={() => setFinder(false)}><form onSubmit={e => { e.preventDefault(); if(matches[0]) go(matches[0][0]); }}><label className="search-field"><Search size={18}/><input autoFocus aria-label="Search pages" placeholder="Users, resources, audit…" value={query} onChange={e=>setQuery(e.target.value)}/></label></form><div className="page-results">{matches.map(([path,label,Icon]) => <button key={path} onClick={()=>go(path)}><Icon size={19}/><span>{label}</span><ArrowRight size={16}/></button>)}{matches.length===0&&<Empty text="No matching pages. Try users, access, or audit."/>}</div><p className="form-hint">Enter to open the first result · Tab to choose · Esc to close</p></Modal>}
  </div>;
}
