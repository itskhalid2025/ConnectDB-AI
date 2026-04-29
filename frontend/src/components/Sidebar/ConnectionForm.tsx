'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { api, ApiError } from '@/lib/api';
import { useSession } from '@/store/sessionStore';

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

  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<'test' | 'connect' | null>(null);

  const isConnected = connectionState === 'connected';

  const handleTest = async () => {
    setBusy('test');
    setError(null);
    setTestStatus(null);
    try {
      const r = await api.testConnection(credentials);
      setTestStatus(r.ok ? `Connected — Postgres ${r.server_version}` : null);
      if (!r.ok && r.error) setError(r.error);
    } catch (e) {
      setError(e instanceof ApiError ? e.hint : 'Test failed.');
    } finally {
      setBusy(null);
    }
  };

  const handleConnect = async () => {
    setBusy('connect');
    setError(null);
    setTestStatus(null);
    setConnectionState('connecting');
    try {
      const r = await api.connect(credentials);
      connect(r.session_id, r.schema_summary);
    } catch (e) {
      setConnectionState('disconnected');
      setError(e instanceof ApiError ? e.hint : 'Connection failed.');
    } finally {
      setBusy(null);
    }
  };

  const handleDisconnect = async () => {
    if (!sessionId) return;
    try {
      await api.deleteSession(sessionId);
    } catch {
      // Best effort — server may have already evicted.
    }
    disconnect();
  };

  return (
    <Card title="PostgreSQL connection">
      <div className="flex flex-col gap-2">
        <Input
          label="Host"
          value={credentials.host}
          onChange={(e) => setCredentials({ host: e.target.value })}
          disabled={isConnected}
        />
        <Input
          label="Port"
          type="number"
          value={credentials.port}
          onChange={(e) => setCredentials({ port: Number(e.target.value || 5432) })}
          disabled={isConnected}
        />
        <Input
          label="Database"
          value={credentials.database}
          onChange={(e) => setCredentials({ database: e.target.value })}
          disabled={isConnected}
        />
        <Input
          label="User"
          value={credentials.user}
          onChange={(e) => setCredentials({ user: e.target.value })}
          disabled={isConnected}
        />
        <Input
          label="Password"
          type="password"
          value={credentials.password}
          onChange={(e) => setCredentials({ password: e.target.value })}
          disabled={isConnected}
        />

        {testStatus && <p className="text-xs text-emerald-400 mt-1">{testStatus}</p>}
        {error && <p className="text-xs text-danger mt-1">{error}</p>}

        <div className="flex gap-2 mt-2">
          {isConnected ? (
            <Button variant="secondary" fullWidth onClick={handleDisconnect}>
              Disconnect
            </Button>
          ) : (
            <>
              <Button
                variant="secondary"
                onClick={handleTest}
                disabled={busy !== null}
                className="flex-1"
              >
                {busy === 'test' ? 'Testing…' : 'Test'}
              </Button>
              <Button
                onClick={handleConnect}
                disabled={busy !== null || !credentials.database || !credentials.user}
                className="flex-1"
              >
                {busy === 'connect' ? 'Connecting…' : 'Connect'}
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
