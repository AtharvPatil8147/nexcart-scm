import { Link } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

export default function Unauthorized() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-base px-6">
      <section className="max-w-md rounded-card border border-border bg-bg-card p-8 text-center">
        <ShieldAlert className="mx-auto mb-4 h-10 w-10 text-accent-danger" />
        <h1 className="text-xl font-semibold text-text-primary">Access denied</h1>
        <p className="mt-2 text-sm text-text-secondary">Your account does not have permission to access this page.</p>
        <Link to="/dashboard" className="mt-6 inline-block rounded-xl bg-accent-purple px-4 py-2 text-sm font-semibold text-white">Return to dashboard</Link>
      </section>
    </main>
  );
}
