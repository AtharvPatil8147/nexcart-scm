import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { UserPlus, Search, Shield, KeyRound, Ban, CheckCircle, RefreshCw } from 'lucide-react';
import {
  getUsers, createUser, updateUser, setUserStatus, resetUserPassword, getAuditLogs,
} from '../api/client';
import { useAuth } from '../auth/AuthContext';

const ROLES = [
  ['admin','Admin'],
  ['manager','Manager'],
  ['viewer','Viewer'],
];

function Modal({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-card border border-border bg-bg-card p-6 shadow-2xl">
        <h2 className="mb-5 text-sm font-semibold text-text-primary">{title}</h2>
        {children}
      </div>
    </div>
  );
}

export default function UserManagement() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [resetTarget, setResetTarget] = useState(null);
  const [tab, setTab] = useState('users');
  const [form, setForm] = useState({ name: '', email: '', role: 'viewer', password: '' });
  const [error, setError] = useState('');

  const usersQuery = useQuery({
    queryKey: ['users', search, roleFilter, statusFilter],
    queryFn: () => getUsers({ search, role: roleFilter, status: statusFilter }),
  });
  const auditQuery = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => getAuditLogs(),
    enabled: tab === 'audit',
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      setCreateOpen(false); setForm({ name: '', email: '', role: 'viewer', password: '' }); setError('');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err) => setError(err.response?.data?.detail || 'Unable to create user'),
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateUser(id, data),
    onSuccess: () => { setEditUser(null); queryClient.invalidateQueries({ queryKey: ['users'] }); },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, active }) => setUserStatus(id, active),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });
  const resetMutation = useMutation({
    mutationFn: ({ id, password }) => resetUserPassword(id, password),
    onSuccess: () => setResetTarget(null),
  });

  const submitCreate = (event) => {
    event.preventDefault();
    createMutation.mutate(form);
  };
  const roleLabel = (role) => ROLES.find(([value]) => value === role)?.[1] || role;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-xl border border-border bg-bg-card p-1">
          {[['users','Users'],['audit','Audit log']].map(([value, label]) => (
            <button key={value} onClick={() => setTab(value)} className={`rounded-lg px-3 py-2 text-xs font-semibold ${tab === value ? 'bg-accent-purple/15 text-accent-purple' : 'text-text-secondary'}`}>{label}</button>
          ))}
        </div>
        {tab === 'users' && (
          <button onClick={() => setCreateOpen(true)} className="flex items-center gap-2 rounded-xl bg-accent-purple px-4 py-2.5 text-xs font-semibold text-white">
            <UserPlus className="h-4 w-4" />Create user
          </button>
        )}
      </div>

      {tab === 'users' ? (
        <>
          <div className="grid gap-3 rounded-card border border-border bg-bg-card p-4 md:grid-cols-[1fr_220px_180px]">
            <div className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-text-secondary" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name or email" className="w-full rounded-xl border border-border bg-bg-base py-2 pl-9 pr-3 text-sm text-text-primary" /></div>
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary"><option value="">All roles</option>{ROLES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary"><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>
          </div>
          <div className="overflow-x-auto rounded-card border border-border bg-bg-card">
            <table className="w-full text-left">
              <thead><tr className="border-b border-border text-xs text-text-secondary"><th className="px-4 py-3">User</th><th className="px-4 py-3">Role</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Actions</th></tr></thead>
              <tbody>
                {(usersQuery.data?.items || []).map((account) => (
                  <tr key={account.id} className="border-b border-border/50 text-sm">
                    <td className="px-4 py-3"><p className="font-medium text-text-primary">{account.name}</p><p className="text-xs text-text-secondary">{account.email}</p></td>
                    <td className="px-4 py-3"><span className="rounded-lg bg-accent-purple/10 px-2 py-1 text-xs text-accent-purple">{roleLabel(account.role)}</span></td>
                    <td className="px-4 py-3"><span className={`text-xs ${account.active ? 'text-accent-teal' : 'text-accent-danger'}`}>{account.active ? 'Active' : 'Inactive'}</span></td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button title="Edit" onClick={() => setEditUser(account)} className="rounded-lg p-2 text-text-secondary hover:bg-bg-hover"><Shield className="h-4 w-4" /></button>
                        <button title="Reset password" onClick={() => setResetTarget(account)} className="rounded-lg p-2 text-text-secondary hover:bg-bg-hover"><KeyRound className="h-4 w-4" /></button>
                        <button disabled={account.id === currentUser?.id} title={account.active ? 'Deactivate' : 'Reactivate'} onClick={() => statusMutation.mutate({ id: account.id, active: !account.active })} className="rounded-lg p-2 text-text-secondary hover:bg-bg-hover disabled:opacity-30">{account.active ? <Ban className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="rounded-card border border-border bg-bg-card p-4">
          <button onClick={() => auditQuery.refetch()} className="mb-3 flex items-center gap-2 text-xs text-text-secondary"><RefreshCw className="h-3.5 w-3.5" />Refresh</button>
          <div className="space-y-2">{(auditQuery.data?.items || []).map((item) => <div key={item._id} className="rounded-lg border border-border/50 p-3"><p className="text-xs font-medium text-text-primary">{item.action} — {item.resource}</p><p className="text-[11px] text-text-secondary">{item.actor_email || 'System'} • {item.timestamp}</p></div>)}</div>
        </div>
      )}

      <Modal open={createOpen} title="Create user" onClose={() => setCreateOpen(false)}>
        <form onSubmit={submitCreate} className="space-y-3">
          {error && <p className="rounded-lg bg-accent-danger/10 p-2 text-xs text-accent-danger">{error}</p>}
          <input required value={form.name} onChange={(e) => setForm({...form,name:e.target.value})} placeholder="Full name" className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary" />
          <input required type="email" value={form.email} onChange={(e) => setForm({...form,email:e.target.value})} placeholder="Email" className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary" />
          <select value={form.role} onChange={(e) => setForm({...form,role:e.target.value})} className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary">{ROLES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
          <input required minLength={12} type="password" value={form.password} onChange={(e) => setForm({...form,password:e.target.value})} placeholder="Temporary password (12+ characters)" className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary" />
          <div className="flex justify-end gap-2 pt-2"><button type="button" onClick={() => setCreateOpen(false)} className="rounded-xl px-4 py-2 text-xs text-text-secondary">Cancel</button><button type="submit" className="rounded-xl bg-accent-purple px-4 py-2 text-xs font-semibold text-white">Create</button></div>
        </form>
      </Modal>

      <Modal open={Boolean(editUser)} title={`Edit ${editUser?.name || 'user'}`} onClose={() => setEditUser(null)}>
        {editUser && <form onSubmit={(e) => {e.preventDefault(); updateMutation.mutate({id:editUser.id,data:{name:e.currentTarget.name.value,role:e.currentTarget.role.value}})}} className="space-y-3">
          <input name="name" defaultValue={editUser.name} className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary" />
          <select name="role" defaultValue={editUser.role} className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary">{ROLES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
          <div className="flex justify-end gap-2"><button type="button" onClick={() => setEditUser(null)} className="rounded-xl px-4 py-2 text-xs text-text-secondary">Cancel</button><button type="submit" className="rounded-xl bg-accent-purple px-4 py-2 text-xs font-semibold text-white">Save</button></div>
        </form>}
      </Modal>

      <Modal open={Boolean(resetTarget)} title={`Reset password: ${resetTarget?.name || ''}`} onClose={() => setResetTarget(null)}>
        {resetTarget && <form onSubmit={(e) => {e.preventDefault(); resetMutation.mutate({id:resetTarget.id,password:e.currentTarget.password.value})}} className="space-y-3">
          <input name="password" required minLength={12} type="password" placeholder="New password (12+ characters)" className="w-full rounded-xl border border-border bg-bg-base px-3 py-2.5 text-sm text-text-primary" />
          <div className="flex justify-end gap-2"><button type="button" onClick={() => setResetTarget(null)} className="rounded-xl px-4 py-2 text-xs text-text-secondary">Cancel</button><button type="submit" className="rounded-xl bg-accent-danger px-4 py-2 text-xs font-semibold text-white">Reset</button></div>
        </form>}
      </Modal>
    </div>
  );
}
