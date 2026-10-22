import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, Users, KeyRound, Database, ScanLine, ListFilter, Menu, ArrowUpRight, X } from 'lucide-react';
const nav = [ ['/', 'Dashboard', LayoutDashboard], ['/users', 'Users', Users], ['/roles', 'Roles & permissions', KeyRound], ['/resources', 'Resources', Database], ['/access', 'Access evaluation', ScanLine], ['/audit', 'Audit explorer', ListFilter] ] as const;
export default function App() {
  const [open, setOpen] = useState(false);
  return <div className="app"><a className="skip-link" href="#main">Skip to content</a><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setOpen(true)}><Menu/></button>{open && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setOpen(false)}/>}
    <aside className={open ? 'sidebar open' : 'sidebar'}><NavLink className="brand" to="/" onClick={() => setOpen(false)}><div className="brand-mark"><ShieldCheck size={25}/></div><div>AccessLedger<small>Access & accountability</small></div></NavLink><button className="mobile-close icon-button" aria-label="Close navigation" onClick={() => setOpen(false)}><X/></button><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{nav.map(([path,label,Icon]) => <NavLink key={path} to={path} end={path==='/'} onClick={() => setOpen(false)}><Icon size={18}/><span>{label}</span>{path==='/access' && <ArrowUpRight className="nav-arrow" size={14}/>}</NavLink>)}</nav><div className="sidebar-footer"><span className="local-dot"/>Local demonstration<small>BCSE302L / BCSE302P<br/>Database Systems · VIT Vellore</small></div></aside>
    <div className="workspace"><div className="topbar"><span>Access management <span className="slash">/</span> <strong>Organization</strong></span><div className="workspace-chip"><span className="local-dot"/>Local workspace</div></div><main id="main"><Outlet/></main><footer className="page-footer">AccessLedger <span>Academic demonstration · Times shown in your local timezone</span></footer></div>
  </div>;
}
