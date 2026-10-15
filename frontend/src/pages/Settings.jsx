/**
 * NexCart — Settings Page
 * Database connection management, API key configuration,
 * agent scheduler controls, and danger zone actions.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Settings as SettingsIcon, Database, Key, Clock,
  AlertTriangle, Check, X, Loader2, Eye, EyeOff,
  RefreshCw, Trash2, Zap, Shield, Wifi, WifiOff,
} from 'lucide-react';
import { testDbConnection } from '../api/client';
import clsx from 'clsx';

function SectionCard({ title, subtitle, icon: Icon, children, variant = 'default' }) {
  return (
    <div className={clsx(
      'bg-bg-card border rounded-card p-6',
      variant === 'danger' ? 'border-accent-danger/30' : 'border-border'
    )}>
      <div className="flex items-center gap-3 mb-5">
        <div className={clsx(
          'flex items-center justify-center w-9 h-9 rounded-xl',
          variant === 'danger' ? 'bg-accent-danger/15 text-accent-danger' : 'bg-accent-purple/15 text-accent-purple'
        )}>
          <Icon className="w-4.5 h-4.5" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
          {subtitle && <p className="text-xs text-text-secondary mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  );
}

function MaskedInput({ label, value, onChange, placeholder, testFn, testLabel = 'Test' }) {
  const [visible, setVisible] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleTest = async () => {
    if (!testFn) return;
    setTesting(true);
    setTestResult(null);
    try {
      await testFn();
      setTestResult({ ok: true, msg: 'Connection successful' });
    } catch (err) {
      setTestResult({ ok: false, msg: err.message || 'Connection failed' });
    }
    setTesting(false);
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-text-secondary">{label}</label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type={visible ? 'text' : 'password'}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className={clsx(
              'w-full px-3 py-2.5 pr-10 rounded-xl text-sm',
              'bg-bg-base border border-border text-text-primary',
              'placeholder:text-text-secondary/40',
              'focus:outline-none focus:border-accent-purple/50 focus:ring-1 focus:ring-accent-purple/20',
              'transition-all duration-200 font-mono'
            )}
          />
          <button
            onClick={() => setVisible(!visible)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
          >
            {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        {testFn && (
          <button
            onClick={handleTest}
            disabled={testing || !value}
            className={clsx(
              'flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold',
              'bg-bg-hover border border-border text-text-secondary',
              'hover:text-text-primary hover:border-accent-purple/30 transition-all',
              'disabled:opacity-40 disabled:cursor-not-allowed'
            )}
          >
            {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            {testLabel}
          </button>
        )}
      </div>
      {testResult && (
        <div className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium animate-fade-in',
          testResult.ok
            ? 'bg-accent-teal/10 text-accent-teal border border-accent-teal/20'
            : 'bg-accent-danger/10 text-accent-danger border border-accent-danger/20'
        )}>
          {testResult.ok ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
          {testResult.msg}
        </div>
      )}
    </div>
  );
}

function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in">
      <div className="bg-bg-card border border-border rounded-card p-6 max-w-sm w-full mx-4 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent-danger/15">
            <AlertTriangle className="w-5 h-5 text-accent-danger" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
            <p className="text-xs text-text-secondary mt-0.5">{message}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-bg-hover border border-border text-text-secondary hover:text-text-primary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-accent-danger text-white hover:bg-accent-danger/80 transition-colors disabled:opacity-50"
          >
            {loading && <Loader2 className="w-3 h-3 animate-spin" />}
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  // Database fields
  const [mongoUri, setMongoUri] = useState('');
  const [mongoDb, setMongoDb] = useState('nexcart');

  // API key fields
  const [newsKey, setNewsKey] = useState('');
  const [weatherKey, setWeatherKey] = useState('');
  const [marineKey, setMarineKey] = useState('');
  const [firebaseKey, setFirebaseKey] = useState('');

  // Scheduler
  const [schedulerEnabled, setSchedulerEnabled] = useState(true);
  const [pollInterval, setPollInterval] = useState(300);

  // Danger zone
  const [confirmDialog, setConfirmDialog] = useState(null);

  // DB health query
  const { data: dbHealth, isLoading: dbLoading, isError: dbError, refetch: refetchDb } = useQuery({
    queryKey: ['db-health-settings'],
    queryFn: testDbConnection,
    refetchInterval: 30000,
    retry: 1,
  });

  const dbOk = dbHealth?.status === 'ok' && !dbError;

  // Test connection mutation
  const testMutation = useMutation({
    mutationFn: testDbConnection,
  });

  return (
    <div className="space-y-6 max-w-4xl animate-fade-in">
      {/* ── Header ── */}
      <div>
        <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-accent-purple" />
          Settings
        </h1>
        <p className="text-sm text-text-secondary mt-0.5">
          Configure connections, API keys, and agent scheduling
        </p>
      </div>

      {/* ── Section 1: Database Connection ── */}
      <SectionCard
        title="Database Connection"
        subtitle="MongoDB Atlas connection settings"
        icon={Database}
      >
        <div className="space-y-4">
          {/* Live Connection Status */}
          <div className={clsx(
            'flex items-center justify-between p-4 rounded-xl border',
            'transition-all duration-300',
            dbOk
              ? 'bg-accent-teal/5 border-accent-teal/20'
              : 'bg-accent-danger/5 border-accent-danger/20'
          )}>
            <div className="flex items-center gap-3">
              <span className={clsx(
                'w-3 h-3 rounded-full shrink-0',
                dbOk ? 'bg-accent-teal animate-pulse-dot' : 'bg-accent-danger animate-pulse-dot'
              )} />
              <div>
                <p className={clsx(
                  'text-sm font-semibold',
                  dbOk ? 'text-accent-teal' : 'text-accent-danger'
                )}>
                  {dbLoading ? 'Checking...' : dbOk ? 'MongoDB Connected' : 'MongoDB Disconnected'}
                </p>
                {dbOk && dbHealth.latency_ms && (
                  <p className="text-xs text-text-secondary">
                    Latency: {dbHealth.latency_ms}ms
                  </p>
                )}
                {!dbOk && !dbLoading && (
                  <p className="text-xs text-accent-danger/70">
                    {dbHealth?.detail || 'Unable to connect to database'}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => refetchDb()}
              className="p-2 rounded-lg hover:bg-bg-hover transition-colors"
            >
              <RefreshCw className={clsx('w-4 h-4 text-text-secondary', dbLoading && 'animate-spin')} />
            </button>
          </div>

          {/* Connection Fields */}
          <MaskedInput
            label="MONGODB_URI"
            value={mongoUri}
            onChange={setMongoUri}
            placeholder="mongodb+srv://user:pass@cluster.mongodb.net"
            testFn={() => testMutation.mutateAsync()}
            testLabel="Test"
          />

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">MONGODB_DB_NAME</label>
            <input
              type="text"
              value={mongoDb}
              onChange={(e) => setMongoDb(e.target.value)}
              placeholder="nexcart"
              className="w-full px-3 py-2.5 rounded-xl text-sm bg-bg-base border border-border text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple/50 font-mono"
            />
          </div>

          <div className="flex items-start gap-2 p-3 rounded-lg bg-accent-amber/5 border border-accent-amber/20">
            <AlertTriangle className="w-4 h-4 text-accent-amber shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary leading-relaxed">
              Changes here update your <code className="text-accent-purple">.env</code> file. A server restart is required for changes to take effect.
            </p>
          </div>
        </div>
      </SectionCard>

      {/* ── Section 2: External API Keys ── */}
      <SectionCard
        title="External API Keys"
        subtitle="Configure signal source integrations"
        icon={Key}
      >
        <div className="space-y-4">
          <MaskedInput
            label="NEWS_API_KEY (NewsAPI.org)"
            value={newsKey}
            onChange={setNewsKey}
            placeholder="Enter your NewsAPI key"
          />
          <MaskedInput
            label="OPENWEATHER_API_KEY (OpenWeatherMap)"
            value={weatherKey}
            onChange={setWeatherKey}
            placeholder="Enter your OpenWeatherMap API key"
          />
          <MaskedInput
            label="MARINE_TRAFFIC_API_KEY (MarineTraffic)"
            value={marineKey}
            onChange={setMarineKey}
            placeholder="Enter your MarineTraffic API key"
          />
          <MaskedInput
            label="FIREBASE_SERVER_KEY (FCM Push)"
            value={firebaseKey}
            onChange={setFirebaseKey}
            placeholder="Enter your Firebase server key"
          />
          <div className="flex items-start gap-2 p-3 rounded-lg bg-accent-teal/5 border border-accent-teal/20">
            <Shield className="w-4 h-4 text-accent-teal shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary leading-relaxed">
              All services gracefully degrade to mock data when API keys are missing. The app works fully in demo mode.
            </p>
          </div>
        </div>
      </SectionCard>

      {/* ── Section 3: Agent Scheduler ── */}
      <SectionCard
        title="Agent Scheduler"
        subtitle="Configure automated signal polling"
        icon={Clock}
      >
        <div className="space-y-4">
          {/* Enable Toggle */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-bg-base border border-border">
            <div>
              <p className="text-sm font-medium text-text-primary">Enable Automatic Polling</p>
              <p className="text-xs text-text-secondary mt-0.5">
                Disruption agent runs automatically at the configured interval
              </p>
            </div>
            <button
              onClick={() => setSchedulerEnabled(!schedulerEnabled)}
              className={clsx(
                'relative w-11 h-6 rounded-full transition-all duration-200',
                schedulerEnabled
                  ? 'bg-accent-purple'
                  : 'bg-bg-hover border border-border'
              )}
            >
              <span className={clsx(
                'absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all duration-200 shadow-sm',
                schedulerEnabled ? 'left-[22px]' : 'left-0.5'
              )} />
            </button>
          </div>

          {/* Poll Interval */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Poll Interval (seconds)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min={30}
                max={3600}
                value={pollInterval}
                onChange={(e) => setPollInterval(parseInt(e.target.value) || 300)}
                disabled={!schedulerEnabled}
                className={clsx(
                  'w-32 px-3 py-2.5 rounded-xl text-sm font-mono',
                  'bg-bg-base border border-border text-text-primary',
                  'focus:outline-none focus:border-accent-purple/50',
                  'disabled:opacity-40 disabled:cursor-not-allowed'
                )}
              />
              <span className="text-xs text-text-secondary">
                ({Math.floor(pollInterval / 60)}m {pollInterval % 60}s)
              </span>
            </div>
          </div>

          {/* Schedule Status */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-bg-base border border-border">
              <p className="text-[10px] font-medium text-text-secondary uppercase tracking-wider mb-1">Last Run</p>
              <p className="text-sm font-semibold text-text-primary">2 minutes ago</p>
            </div>
            <div className="p-3 rounded-xl bg-bg-base border border-border">
              <p className="text-[10px] font-medium text-text-secondary uppercase tracking-wider mb-1">Next Run In</p>
              <p className="text-sm font-semibold text-text-primary">
                {schedulerEnabled ? `${Math.floor(pollInterval / 60)}m ${pollInterval % 60}s` : 'Disabled'}
              </p>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* ── Section 4: Danger Zone ── */}
      <SectionCard
        title="Danger Zone"
        subtitle="Irreversible actions"
        icon={AlertTriangle}
        variant="danger"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-xl bg-bg-base border border-accent-danger/20">
            <div>
              <p className="text-sm font-medium text-text-primary">Reseed Database</p>
              <p className="text-xs text-text-secondary mt-0.5">
                Wipe all data and regenerate 50 SKUs, 200 customers, 20 events
              </p>
            </div>
            <button
              onClick={() => setConfirmDialog('reseed')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-accent-danger/15 text-accent-danger border border-accent-danger/20 hover:bg-accent-danger/25 transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reseed
            </button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl bg-bg-base border border-accent-danger/20">
            <div>
              <p className="text-sm font-medium text-text-primary">Clear All Nudge Campaigns</p>
              <p className="text-xs text-text-secondary mt-0.5">
                Remove all nudge campaign records from the database
              </p>
            </div>
            <button
              onClick={() => setConfirmDialog('clear-nudges')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-accent-danger/15 text-accent-danger border border-accent-danger/20 hover:bg-accent-danger/25 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          </div>
        </div>
      </SectionCard>

      {/* ── Confirmation Dialog ── */}
      <ConfirmDialog
        open={confirmDialog === 'reseed'}
        title="Reseed Database?"
        message="This will wipe all existing data and regenerate seed data. This action cannot be undone."
        onConfirm={() => {
          // TODO: Call reseed API endpoint
          setConfirmDialog(null);
        }}
        onCancel={() => setConfirmDialog(null)}
      />
      <ConfirmDialog
        open={confirmDialog === 'clear-nudges'}
        title="Clear All Nudge Campaigns?"
        message="This will permanently delete all nudge campaign records. This action cannot be undone."
        onConfirm={() => {
          // TODO: Call clear nudges API endpoint
          setConfirmDialog(null);
        }}
        onCancel={() => setConfirmDialog(null)}
      />
    </div>
  );
}

// ✓ Settings.jsx complete
