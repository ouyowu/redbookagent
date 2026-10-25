export type ModelId = 'gemini'

interface GeminiConfig {
  provider: 'gemini'
  label: string
  badge: string
  badgeColor: string
  apiKey: string
  model: string
}

export type ModelConfig = GeminiConfig

// Server-side only (uses process.env) — do NOT import in client components
export const MODELS: Record<ModelId, ModelConfig> = {
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
  gemini: { label: 'Gemini 2.0 Flash', badge: 'Google', badgeColor: '#1d6fd8' },
}

export const MODEL_IDS = Object.keys(MODEL_META) as ModelId[]
