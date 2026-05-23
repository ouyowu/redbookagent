export type ModelId = 'chatgpt' | 'gemini'

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
  chatgpt: {
    provider: 'openai-compat',
    label: 'GPT-4o',
    badge: 'OpenAI',
    badgeColor: '#10a37f',
    baseURL: 'https://api.openai.com/v1',
    apiKey: process.env.OPENAI_API_KEY ?? '',
    model: 'gpt-4o',
  },
  gemini: {
    provider: 'gemini',
    label: 'Gemini 2.0 Flash',
    badge: 'Google',
    badgeColor: '#1d6fd8',
    apiKey: process.env.GOOGLE_AI_API_KEY ?? '',
    model: 'gemini-2.0-flash',
  },
}

// Safe for client-side import (no secrets)
export const MODEL_META: Record<ModelId, { label: string; badge: string; badgeColor: string }> = {
  chatgpt: { label: 'GPT-4o',           badge: 'OpenAI', badgeColor: '#10a37f' },
  gemini:  { label: 'Gemini 2.0 Flash', badge: 'Google', badgeColor: '#1d6fd8' },
}

export const MODEL_IDS = Object.keys(MODEL_META) as ModelId[]
