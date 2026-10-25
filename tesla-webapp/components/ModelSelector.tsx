'use client'

import { MODEL_META } from '@/lib/models'

// Single-model display — no dropdown needed when only Gemini is available
export function ModelSelector() {
  const m = MODEL_META.gemini
  return (
    <div
      className="flex items-center gap-2 px-4 py-1.5 rounded-xl border border-tesla-border bg-tesla-surface"
      style={{ borderColor: m.badgeColor + '55' }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: m.badgeColor }}
      />
      <span className="text-tesla-text text-mcu-sm font-semibold">{m.label}</span>
      <span
        className="px-2 py-0.5 rounded-full text-mcu-sm font-bold text-white"
        style={{ backgroundColor: m.badgeColor }}
      >
        {m.badge}
      </span>
    </div>
  )
}
