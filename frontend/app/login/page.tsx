'use client';

import type { FormEvent } from 'react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { LogIn, ShieldCheck } from 'lucide-react';
import AppShell from '../components/AppShell';
import { DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, login } from '../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState(DEFAULT_ADMIN_EMAIL);
  const [password, setPassword] = useState(DEFAULT_ADMIN_PASSWORD);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      const next = new URLSearchParams(window.location.search).get('next') || '/';
      router.push(next.startsWith('/') ? next : '/');
    } catch {
      setError('Login failed. Check the analyst email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell active="dashboard" statusText="Analyst login">
      <section className="auth-layout">
        <article className="panel auth-panel">
          <div className="brand-mark"><ShieldCheck size={22} /></div>
          <p className="section-label">SentinelX access control</p>
          <h1>Sign in to manage incidents and protected SOC actions.</h1>
          <form className="auth-form" onSubmit={submit}>
            <label>
              Analyst email
              <input value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <label>
              Password
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            {error && <p className="form-error">{error}</p>}
            <button className="primary-button" type="submit" disabled={loading || !email || !password}>
              <LogIn size={16} />
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
            <Link className="text-link" href="/signup">New analyst? Create an account</Link>
          </form>
        </article>
      </section>
    </AppShell>
  );
}
