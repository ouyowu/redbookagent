'use client'

import { MODEL_IDS, MODEL_META, type ModelId } from '@/lib/models'

interface Props {
  value: ModelId
  onChange: (model: ModelId) => void
  disabled?: boolean
}

export function ModelSelector({ value, onChange, disabled }: Props) {
  const current = MODEL_META[value]

  return (
    <div className="flex items-center gap-3">
      <span
        className="px-3 py-1 rounded-full text-mcu-sm font-semibold text-white"
        style={{ backgroundColor: current.badgeColor }}
      >
        {current.badge}
      </span>

      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value as ModelId)}
        className={[
          'bg-tesla-surface border border-tesla-border rounded-xl',
          'text-tesla-text text-mcu-base font-medium',
          'px-4 py-2 outline-none cursor-pointer',
          'focus:border-tesla-accent transition-colors',
          disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-tesla-muted',
        ].join(' ')}
      >
        {MODEL_IDS.map((id) => (
          <option key={id} value={id}>
            {MODEL_META[id].label}
          </option>
        ))}
      </select>
    </div>
  )
}
