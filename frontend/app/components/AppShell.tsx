'use client';

import Link from 'next/link';
import type { ComponentType, ReactNode } from 'react';
import { BarChart3, Bot, ClipboardCheck, FilePlus2, FileText, LogIn, Network, ShieldCheck } from 'lucide-react';

type NavKey = 'dashboard' | 'intake' | 'investigate' | 'assistant' | 'reports' | 'readiness';

const navItems: Array<{ key: NavKey; label: string; href: string; icon: ComponentType<{ size?: number }> }> = [
  { key: 'dashboard', label: 'Dashboard', href: '/', icon: BarChart3 },
  { key: 'intake', label: 'Intake', href: '/intake', icon: FilePlus2 },
  { key: 'investigate', label: 'Investigate', href: '/investigate', icon: Network },
  { key: 'assistant', label: 'AI Assistant', href: '/assistant', icon: Bot },
  { key: 'reports', label: 'Reports', href: '/reports', icon: FileText },
  { key: 'readiness', label: 'Readiness', href: '/readiness', icon: ClipboardCheck },
];

export default function AppShell({
  active,
  children,
  statusText = 'Live SOC',
}: {
  active: NavKey;
  children: ReactNode;
  statusText?: string;
}) {
  return (
    <div className="app-frame">
      <header className="topbar">
        <Link href="/" className="brand" aria-label="SentinelX home">
          <span className="brand-mark"><ShieldCheck size={20} /></span>
          <span>
            <strong>SentinelX</strong>
            <small>Autonomous threat hunting</small>
          </span>
        </Link>

        <nav className="main-nav" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link className={active === item.key ? 'active' : ''} href={item.href} key={item.key}>
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="status-chip">
          <span />
          {statusText}
        </div>
        <Link href="/login" className="login-link" aria-label="Analyst login">
          <LogIn size={15} />
          Login
        </Link>
      </header>

      <main className="page-shell">{children}</main>
    </div>
  );
}
