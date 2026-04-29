/**
 * File: AIConfigPanel.tsx
 * Version: 1.1.0
 * Created At: 2026-04-25
 * Updated At: 2026-04-29
 * Description: Component for managing Large Language Model (LLM) settings.
 *              Handles provider selection, secure API key entry, and 
 *              dynamic model discovery via the backend.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { api, ApiError } from '@/lib/api';
import type { Provider } from '@/lib/types';
import { useSession } from '@/store/sessionStore';

/** Available AI providers supported by the backend adapters. */
const PROVIDERS: { value: Provider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'anthropic', label: 'Claude (Anthropic)' },
];

/**
 * AIConfigPanel Component
 * 
 * Provides the configuration surface for the "brain" of the application.
 * Users must provide a valid API key to fetch and select specific models.
 */
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

  /**
   * Contacts the backend to retrieve the list of models supported 
   * by the current provider and API key.
   */
  const fetchModels = async () => {
    if (!apiKey) {
      setError('Please provide an API key to discover models.');
      return;
    }
    setError(null);
    setModelsLoading(true);
    try {
      const r = await api.listModels(provider, apiKey);
      setModels(r.models);
      lastFetchKey.current = `${provider}:${apiKey}`;
    } catch (e) {
      setError(e instanceof ApiError ? e.hint : 'Credential validation failed.');
      setModels([]);
    } finally {
      setModelsLoading(false);
    }
  };

  /**
   * Security/UX Guard: Invalidate model list if provider or key changes 
   * after a successful fetch to prevent cross-provider configuration errors.
   */
  useEffect(() => {
    const currentKey = `${provider}:${apiKey}`;
    if (lastFetchKey.current && lastFetchKey.current !== currentKey) {
      setModels([]);
    }
  }, [provider, apiKey, setModels]);

  return (
    <Card title="Intelligence Engine">
      <div className="flex flex-col gap-3">
        {/* Provider Selection */}
        <Select
          label="AI Service Provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value as Provider)}
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </Select>

        {/* API Key Input */}
        <Input
          label="API Secret Key"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
        />

        {/* Discovery Action */}
        <Button
          variant="secondary"
          onClick={fetchModels}
          disabled={modelsLoading || !apiKey}
          className="text-xs font-semibold py-1 h-8"
        >
          {modelsLoading ? 'Querying Models...' : 'Synchronize Models'}
        </Button>

        {/* Model Selection */}
        <Select
          label="Active Model"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          disabled={models.length === 0}
        >
          <option value="">
            {models.length ? 'Select Analysis Model' : '— Models Not Synced —'}
          </option>
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </Select>

        {/* Error Feedback */}
        {error && (
          <p className="text-[10px] text-red-400 font-medium animate-in fade-in slide-in-from-top-1">
            {error}
          </p>
        )}
      </div>
    </Card>
  );
}
