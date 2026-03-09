import { Link, useLocation } from 'react-router-dom';
import { useThemeStore } from '../store';
import {
  HomeIcon,
  CalendarDaysIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
} from '@heroicons/react/24/outline';

const navItems = [
  { path: '/',         label: 'Dashboard', icon: HomeIcon },
  { path: '/meetings', label: 'Meetings',  icon: CalendarDaysIcon },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location  = useLocation();
  const { dark, toggle } = useThemeStore();
  const pageLabel = navItems.find((n) => n.path === location.pathname)?.label ?? 'Dashboard';

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#0d1117]">

      {/* ════════════════════ SIDEBAR ════════════════════ */}
      <aside className="hidden md:flex md:flex-col w-[260px] bg-white dark:bg-[#161b27] border-r border-slate-100 dark:border-slate-800">

        {/* Sidebar Header / Brand area */}
        <div className="flex items-center gap-3.5 px-6 py-6 border-b border-slate-100 dark:border-slate-800">
          {/* Logo - Properly sized */}
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
                className={`group flex items-center gap-3 px-3.5 py-3 rounded-xl text-[14px] font-semibold transition-all duration-200 ${
                  active
                    ? 'bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 shadow-sm shadow-brand-100/50 dark:shadow-none'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 hover:text-slate-800 dark:hover:text-white'
                }`}
              >
                <div className={`w-8 h-8 flex items-center justify-center rounded-xl transition-all duration-200 ${
                  active
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
        <div className="p-5 border-t border-slate-100 dark:border-slate-800 mt-auto bg-slate-50/50 dark:bg-[#121622]/50">
          <div className="flex items-center gap-3.5">
            <img src="/botivate-logo-cropped.png" alt="Logo" className="w-[32px] h-[32px] object-contain drop-shadow-sm shrink-0" />
            <div className="overflow-hidden flex flex-col justify-center">
              <p className="text-[9px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-widest mb-0.5">Powered by</p>
              <p className="text-[13px] font-extrabold text-slate-800 dark:text-white leading-none truncate">Botivate Services</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ════════════════════ MAIN AREA ════════════════════ */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* ── HEADER — Very Clean, No Double Logo ── */}
        <header className="h-[72px] flex items-center justify-between px-8 bg-white dark:bg-[#161b27] border-b border-slate-100 dark:border-slate-800 shadow-sm shrink-0 z-10">
          
          {/* Left: Dynamic Page Title */}
          <div>
            <h2 className="text-[20px] font-extrabold text-slate-800 dark:text-white leading-tight">{pageLabel}</h2>
            <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">Welcome back to Botivate.</p>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggle}
              className="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-800 dark:hover:text-white transition-all border border-slate-100 dark:border-slate-800"
              aria-label="Toggle theme"
            >
              {dark ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
            </button>
            
            <Link
              to="/notifications"
              className="relative w-10 h-10 flex items-center justify-center rounded-xl bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-800 dark:hover:text-white transition-all border border-slate-100 dark:border-slate-800"
            >
              <BellIcon className="w-5 h-5" />
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 border-2 border-slate-50 dark:border-white/5 rounded-full" />
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-[1400px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
