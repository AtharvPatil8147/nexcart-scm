import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { AlertCircle, LockKeyhole, LogIn, Mail, Zap } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login: authenticate, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const submit = async (event) => {
  event.preventDefault();
  if (loading) return;

  setLoading(true);
  setError('');

  try {
    await authenticate({ email, password });
    navigate('/dashboard', { replace: true });
  } catch (requestError) {
    const detail = requestError.response?.data?.detail;
    const message = Array.isArray(detail)
      ? detail[0]?.msg
      : detail || requestError.message || 'Unable to sign in. Check your connection and credentials.';

    setError(message);
  } finally {
    setLoading(false);
  }
};


  return (
    <main className="min-h-screen bg-bg-base flex items-center justify-center px-4">
      <section className="w-full max-w-md bg-bg-card border border-border rounded-card p-8 shadow-2xl shadow-black/20">
        <div className="flex items-center gap-3 mb-7">
          <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent-purple/20"><Zap className="w-5 h-5 text-accent-purple" /></span>
          <div><h1 className="text-xl font-bold text-text-primary">NexCart</h1><p className="text-xs text-text-secondary">Supply-chain intelligence</p></div>
        </div>
        <h2 className="text-lg font-semibold text-text-primary">Sign in</h2>
        <p className="text-sm text-text-secondary mt-1 mb-6">Use your assigned role-based account to access the dashboard.</p>
        {error && <div className="mb-4 flex gap-2 rounded-xl border border-accent-danger/30 bg-accent-danger/10 p-3 text-xs text-accent-danger"><AlertCircle className="w-4 h-4 shrink-0" />{error}</div>}
        <form className="space-y-4" onSubmit={submit}>
          <label className="block text-xs font-medium text-text-secondary">Email<div className="relative mt-1.5"><Mail className="absolute left-3 top-3 w-4 h-4 text-text-secondary" /><input className="w-full rounded-xl border border-border bg-bg-base py-2.5 pl-10 pr-3 text-sm text-text-primary outline-none focus:border-accent-purple" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div></label>
          <label className="block text-xs font-medium text-text-secondary">Password<div className="relative mt-1.5"><LockKeyhole className="absolute left-3 top-3 w-4 h-4 text-text-secondary" /><input className="w-full rounded-xl border border-border bg-bg-base py-2.5 pl-10 pr-3 text-sm text-text-primary outline-none focus:border-accent-purple" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div></label>
          <button className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent-purple px-4 py-2.5 text-sm font-semibold text-white hover:bg-accent-purple/80 disabled:opacity-50" disabled={loading} type="submit"><LogIn className="w-4 h-4" />{loading ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <div className="mt-6 border-t border-border pt-5">
          <p className="mb-3 text-xs font-medium text-text-secondary">Demo accounts</p>
          <div className="grid grid-cols-3 gap-2">
            {[
              ['Admin', 'admin@nexcart.com', 'Admin@123456'],
              ['Manager', 'manager@nexcart.com', 'Manager@123456'],
              ['Viewer', 'viewer@nexcart.com', 'Viewer@123456'],
            ].map(([label, demoEmail, demoPassword]) => (
              <button
                key={label}
                type="button"
                onClick={() => { setEmail(demoEmail); setPassword(demoPassword); }}
                className="rounded-xl border border-border bg-bg-base px-2 py-2 text-xs font-semibold text-text-secondary hover:border-accent-purple/50 hover:text-text-primary"
              >
                {label}
              </button>
            ))}
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-text-secondary">
            Demo accounts are created automatically outside production mode.
          </p>
        </div>
        <p className="mt-6 text-xs leading-relaxed text-text-secondary">First deployment? Set the bootstrap administrator variables in <code>.env</code>, then restart the backend.</p>
      </section>
    </main>
  );
}
