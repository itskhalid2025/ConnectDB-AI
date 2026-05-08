/**
 * File: ConnectionForm.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Primary interface for configuring PostgreSQL connectivity. 
 *              Manages credential state, validates connectivity via the backend, 
 *              and initiates persistent analysis sessions.
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { api, ApiError } from '@/lib/api';
import { useSession } from '@/store/sessionStore';

/**
 * ConnectionForm Component
 * 
 * Orchestrates the database handshake process. Uses the global session store 
 * to persist credentials and transition between connection states.
 */
export function ConnectionForm() {
  const {
    credentials,
    setCredentials,
    connectionState,
    setConnectionState,
    connect,
    disconnect,
    sessionId,
  } = useSession();

  // Local UI state for feedback loops
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<'test' | 'connect' | null>(null);

  const isConnected = connectionState === 'connected';

  /**
   * Pings the backend to verify the provided credentials.
   * Does not establish a persistent session.
   */
  const handleTest = async () => {
    setBusy('test');
    setError(null);
    setTestStatus(null);
    try {
      const r = await api.testConnection(credentials);
      setTestStatus(r.ok ? `Connection Verified — PostgreSQL ${r.server_version}` : null);
      if (!r.ok && r.error) setError(r.error);
    } catch (e) {
      setError(e instanceof ApiError ? e.hint : 'Testing service unreachable.');
    } finally {
      setBusy(null);
    }
  };

  /**
   * Performs full session initialization.
   * Triggers schema introspection and prepares the SQL generation engine.
   */
  const handleConnect = async () => {
    setBusy('connect');
    setError(null);
    setTestStatus(null);
    setConnectionState('connecting');
    try {
      const r = await api.connect(credentials);
      // Synchronize backend session with local state
      connect(r.session_id, r.schema_summary);
    } catch (e) {
      setConnectionState('disconnected');
      setError(e instanceof ApiError ? e.hint : 'Failed to establish persistent session.');
    } finally {
      setBusy(null);
    }
  };

  /**
   * Gracefully terminates the backend session and clears local state.
   */
  const handleDisconnect = async () => {
    if (!sessionId) return;
    try {
      // Best-effort cleanup on the server
      await api.deleteSession(sessionId);
    } catch {
      /* Best effort: server may have already timed out the session */
    }
    disconnect();
  };

  return (
    <Card title="Database Connection">
      <div className="flex flex-col gap-3">
        {/* Credential Inputs */}
        <div className="space-y-2">
          <Input
            label="Hostname"
            placeholder="e.g. localhost"
            value={credentials.host}
            onChange={(e) => setCredentials({ host: e.target.value })}
            disabled={isConnected}
          />
          <div className="grid grid-cols-3 gap-2">
            <div className="col-span-2">
              <Input
                label="Database Name"
                placeholder="public"
                value={credentials.database}
                onChange={(e) => setCredentials({ database: e.target.value })}
                disabled={isConnected}
              />
            </div>
            <Input
              label="Port"
              type="number"
              value={credentials.port}
              onChange={(e) => setCredentials({ port: Number(e.target.value || 5432) })}
              disabled={isConnected}
            />
          </div>
          <Input
            label="User"
            value={credentials.user}
            onChange={(e) => setCredentials({ user: e.target.value })}
            disabled={isConnected}
          />
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={credentials.password}
            onChange={(e) => setCredentials({ password: e.target.value })}
            disabled={isConnected}
          />
          <Input
            label="Target Schemas"
            placeholder="e.g. public, tenant_abc"
            value={credentials.schemas?.join(', ') || ''}
            onChange={(e) => setCredentials({ 
              schemas: e.target.value ? e.target.value.split(',').map(s => s.trim()) : [] 
            })}
            disabled={isConnected}
          />
        </div>

        {/* Feedback Messages */}
        {testStatus && (
          <div className="text-[10px] text-emerald-400 font-medium bg-emerald-500/5 p-2 rounded border border-emerald-500/20">
            {testStatus}
          </div>
        )}
        {error && (
          <div className="text-[10px] text-red-400 font-medium bg-red-500/5 p-2 rounded border border-red-500/20 leading-relaxed">
            <span className="font-bold uppercase mr-1">Error:</span> {error}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex gap-2 mt-2">
          {isConnected ? (
            <Button variant="secondary" fullWidth onClick={handleDisconnect} className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/20">
              Terminate Session
            </Button>
          ) : (
            <>
              <Button
                variant="secondary"
                onClick={handleTest}
                disabled={busy !== null}
                className="flex-1"
              >
                {busy === 'test' ? 'Verifying...' : 'Test Sync'}
              </Button>
              <Button
                onClick={handleConnect}
                disabled={busy !== null || !credentials.database || !credentials.user}
                className="flex-1 shadow-lg shadow-primary/20"
              >
                {busy === 'connect' ? 'Syncing...' : 'Connect'}
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
