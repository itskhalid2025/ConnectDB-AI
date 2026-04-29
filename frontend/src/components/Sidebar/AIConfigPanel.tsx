'use client';

import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { api, ApiError } from '@/lib/api';
import type { Provider } from '@/lib/types';
import { useSession } from '@/store/sessionStore';

const PROVIDERS: { value: Provider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'anthropic', label: 'Claude (Anthropic)' },
];

export function AIConfigPanel() {
  const {
    provider,
    apiKey,
    model,
    models,
    modelsLoading,
    setProvider,
    setApiKey,
    setModel,
    setModels,
    setModelsLoading,
  } = useSession();

  const [error, setError] = useState<string | null>(null);
  const lastFetchKey = useRef<string>('');

  const fetchModels = async () => {
    if (!apiKey) {
      setError('Enter an API key first.');
      return;
    }
    setError(null);
    setModelsLoading(true);
    try {
      const r = await api.listModels(provider, apiKey);
      setModels(r.models);
      lastFetchKey.current = `${provider}:${apiKey}`;
    } catch (e) {
      setError(e instanceof ApiError ? e.hint : 'Failed to fetch models.');
      setModels([]);
    } finally {
      setModelsLoading(false);
    }
  };

  // Clear model + models if provider/api key changes from what was last fetched.
  useEffect(() => {
    if (lastFetchKey.current && lastFetchKey.current !== `${provider}:${apiKey}`) {
      setModels([]);
    }
  }, [provider, apiKey, setModels]);

  return (
    <Card title="AI provider">
      <div className="flex flex-col gap-2">
        <Select
          label="Provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value as Provider)}
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </Select>

        <Input
          label="API key"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-… / AIza… / sk-ant-…"
        />

        <Button
          variant="secondary"
          onClick={fetchModels}
          disabled={modelsLoading || !apiKey}
        >
          {modelsLoading ? 'Loading models…' : 'Fetch models'}
        </Button>

        <Select
          label="Model"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          disabled={models.length === 0}
        >
          <option value="">{models.length ? 'Select a model' : '— fetch models first —'}</option>
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </Select>

        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    </Card>
  );
}
