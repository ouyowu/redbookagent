export type ModelId = 'grok' | 'gemini' | 'hermes'

interface OpenAICompatConfig {
  provider: 'openai-compat'
  label: string
  badge: string
  badgeColor: string
  baseURL: string
  apiKey: string
  model: string
}

interface GeminiConfig {
  provider: 'gemini'
  label: string
  badge: string
  badgeColor: string
  apiKey: string
  model: string
}

export type ModelConfig = OpenAICompatConfig | GeminiConfig

// Server-side only (uses process.env) — do NOT import in client components
export const MODELS: Record<ModelId, ModelConfig> = {
  grok: {
    provider: 'openai-compat',
    label: 'Grok 3 Mini',
    badge: 'xAI',
    badgeColor: '#7c3aed',
    baseURL: 'https://api.x.ai/v1',
    apiKey: process.env.XAI_API_KEY ?? '',
    model: 'grok-3-mini',
  },
  gemini: {
    provider: 'gemini',
    label: 'Gemini 2.0 Flash',
    badge: 'Google',
    badgeColor: '#1d6fd8',
    apiKey: process.env.GOOGLE_AI_API_KEY ?? '',
    model: 'gemini-2.0-flash',
  },
  hermes: {
    provider: 'openai-compat',
    label: 'Hermes 3 70B',
    badge: 'Together',
    badgeColor: '#059669',
    baseURL: 'https://api.together.xyz/v1',
    apiKey: process.env.TOGETHER_API_KEY ?? '',
    model: 'NousResearch/Hermes-3-Llama-3.1-70B-Turbo',
  },
}

// Safe for client-side import (no secrets)
export const MODEL_META: Record<ModelId, { label: string; badge: string; badgeColor: string }> = {
  grok:   { label: 'Grok 3 Mini',      badge: 'xAI',     badgeColor: '#7c3aed' },
  gemini: { label: 'Gemini 2.0 Flash', badge: 'Google',  badgeColor: '#1d6fd8' },
  hermes: { label: 'Hermes 3 70B',     badge: 'Together', badgeColor: '#059669' },
}

export const MODEL_IDS = Object.keys(MODEL_META) as ModelId[]
