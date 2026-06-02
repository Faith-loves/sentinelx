'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UserPlus } from 'lucide-react';
import AppShell from '../components/AppShell';
import { register } from '../lib/api';

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    setError('');
    try {
      await register(email, name, password);
      router.push('/');
    } catch {
      setError('Signup is disabled or the account already exists. Ask an admin to create your analyst account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell active="dashboard" statusText="Analyst signup">
      <section className="auth-layout">
        <article className="panel auth-panel">
          <p className="section-label">New analyst access</p>
          <h1>Create an analyst account when registration is enabled.</h1>
          <div className="auth-form">
            <label>
              Full name
              <input value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <label>
              Password
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            {error && <p className="form-error">{error}</p>}
            <button className="primary-button" onClick={submit} disabled={loading || !name || !email || !password}>
              <UserPlus size={16} />
              {loading ? 'Creating account...' : 'Create account'}
            </button>
            <Link className="text-link" href="/login">Already have an account? Sign in</Link>
          </div>
        </article>
      </section>
    </AppShell>
  );
}
