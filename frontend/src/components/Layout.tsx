import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../api';
import { useThemeStore } from '../store';
import {
  HomeIcon,
  CalendarDaysIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  ShieldCheckIcon,
  ClipboardDocumentListIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const navItems = [
  { path: '/', label: 'Dashboard', icon: HomeIcon },
  { path: '/meetings', label: 'Meetings', icon: CalendarDaysIcon },
  { path: '/br', label: 'Board Resolutions', icon: ShieldCheckIcon },
  { path: '/tasks', label: 'Global Tasks', icon: ClipboardDocumentListIcon },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { dark, toggle } = useThemeStore();
  const [branding, setBranding] = useState<{ show_botivate_branding: boolean; client_name: string } | null>(null);

  useEffect(() => {
    api.get('/branding/').then(({ data }) => setBranding(data)).catch(() => {});
  }, []);
  const getPageLabel = () => {
    const matched = navItems.find((n) => n.path === location.pathname);
    if (matched) return matched.label;
    
    if (location.pathname.startsWith('/meetings/')) return 'Meeting Details';
    if (location.pathname.startsWith('/br/')) return 'Board Resolution Details';
    if (location.pathname === '/attendance') return 'Attendance Tracking';
    if (location.pathname === '/users') return 'User Management';
    if (location.pathname === '/notifications') return 'Notifications';
    if (location.pathname === '/upload') return 'Record Upload';
    if (location.pathname === '/schedule-meeting') return 'Schedule Meeting';
    if (location.pathname === '/create-mom') return 'Manual Record Entry';
    
    return 'Dashboard';
  };
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pageLabel = getPageLabel();

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#0d1117]">

      {/* ════════════════════ MOBILE SIDEBAR (Overlay) ════════════════════ */}
      <div className={`fixed inset-0 z-50 md:hidden transition-opacity duration-300 ${isMobileMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setIsMobileMenuOpen(false)} />
        <aside className={`absolute left-0 top-0 bottom-0 w-[280px] flex flex-col bg-white dark:bg-[#161b27] shadow-xl transition-transform duration-300 transform ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <img src="/botivate-logo-cropped.png" alt="Logo" className="w-[32px] h-[32px] object-contain" />
              <span className="font-black text-slate-800 dark:text-white">Botivate</span>
            </div>
            <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white">
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          <nav className="p-4 space-y-1">
            {navItems.map(({ path, label, icon: Icon }) => {
              const active = location.pathname === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-semibold transition-all ${active
                    ? 'bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Powered by Footer in Mobile Sidebar */}
          {branding?.show_botivate_branding && (
            <a 
              href="https://botivate.in/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-5 border-t border-slate-100 dark:border-slate-800 mt-auto bg-slate-50/50 dark:bg-[#121622]/50 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors cursor-pointer block"
            >
              <div className="flex items-center gap-3.5">
                <img src="/botivate-logo-cropped.png" alt="Logo" className="w-[32px] h-[32px] object-contain drop-shadow-sm shrink-0" />
                <div className="overflow-hidden flex flex-col justify-center">
                  <p className="text-[9px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-widest mb-0.5">Powered by</p>
                  <p className="text-[13px] font-extrabold text-slate-800 dark:text-white leading-none truncate">Botivate Services</p>
                </div>
              </div>
            </a>
          )}
        </aside>
      </div>

      {/* ════════════════════ SIDEBAR (Desktop) ════════════════════ */}
      <aside className="hidden md:flex md:flex-col w-[260px] bg-white dark:bg-[#161b27] border-r border-slate-100 dark:border-slate-800">
        {/* ... (Desktop sidebar content remains same as before) */}
        {/* Sidebar Header / Brand area */}
        <div className="flex items-center gap-3.5 px-6 py-6 border-b border-slate-100 dark:border-slate-800">
          <img src="/botivate-logo-cropped.png" alt="Botivate Logo" className="w-[38px] h-[38px] object-contain drop-shadow-sm shrink-0" />
          <div className="leading-tight mt-0.5">
            <h1 className="text-[20px] font-black text-slate-800 dark:text-white tracking-tight -mb-1">Botivate</h1>
            <p className="text-[9px] font-bold text-brand-500 uppercase tracking-widest mt-1">Agentic Minutes of Meeting</p>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          <p className="px-3 pb-3 text-[11px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">Menu</p>
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={`group flex items-center gap-3 px-3.5 py-3 rounded-xl text-[14px] font-semibold transition-all duration-200 ${active
                  ? 'bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 shadow-sm shadow-brand-100/50 dark:shadow-none'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 hover:text-slate-800 dark:hover:text-white'
                  }`}
              >
                <div className={`w-8 h-8 flex items-center justify-center rounded-xl transition-all duration-200 ${active
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-200 dark:shadow-brand-900/50 scale-110'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-400 group-hover:bg-slate-200 dark:group-hover:bg-slate-700 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                  }`}>
                  <Icon className="w-4 h-4" />
                </div>
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Powered by Footer in Sidebar */}
        {branding?.show_botivate_branding && (
          <a 
            href="https://botivate.in/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-5 border-t border-slate-100 dark:border-slate-800 mt-auto bg-slate-50/50 dark:bg-[#121622]/50 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors cursor-pointer block"
          >
            <div className="flex items-center gap-3.5">
              <img src="/botivate-logo-cropped.png" alt="Logo" className="w-[32px] h-[32px] object-contain drop-shadow-sm shrink-0" />
              <div className="overflow-hidden flex flex-col justify-center">
                <p className="text-[9px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-widest mb-0.5">Powered by</p>
                <p className="text-[13px] font-extrabold text-slate-800 dark:text-white leading-none truncate">Botivate Services</p>
              </div>
            </div>
          </a>
        )}
      </aside>

      {/* ════════════════════ MAIN AREA ════════════════════ */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* ── HEADER ── */}
        <header className="h-[72px] flex items-center justify-between px-4 md:px-8 bg-white dark:bg-[#161b27] border-b border-slate-100 dark:border-slate-800 shadow-sm shrink-0 z-10">

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsMobileMenuOpen(true)}
              className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5 md:hidden"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <div className="min-w-0">
              <h2 className="text-[16px] md:text-[20px] font-extrabold text-slate-800 dark:text-white leading-tight truncate">{pageLabel}</h2>
              <p className="text-[11px] md:text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">
                Welcome back to {branding?.client_name || 'Botivate'}.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-3">
            <button
              onClick={toggle}
              className="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-xl bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400 border border-slate-100 dark:border-slate-800 shrink-0"
              aria-label="Toggle theme"
            >
              {dark ? <SunIcon className="w-4 md:w-5 h-4 md:h-5" /> : <MoonIcon className="w-4 md:w-5 h-4 md:h-5" />}
            </button>

            <Link
              to="/notifications"
              className="relative w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-xl bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400 border border-slate-100 dark:border-slate-800 shrink-0"
            >
              <BellIcon className="w-4 md:w-5 h-4 md:h-5" />
              <span className="absolute top-2 right-2 md:top-2.5 md:right-2.5 w-2 h-2 bg-red-500 border-2 border-slate-50 dark:border-white/5 rounded-full" />
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 relative">
          <div className="max-w-[1400px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
