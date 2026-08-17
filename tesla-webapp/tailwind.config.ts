import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Tesla MCU dark palette
        tesla: {
          bg:       '#0d0d0d',
          surface:  '#1a1a1a',
          border:   '#2a2a2a',
          accent:   '#e82127', // Tesla red
          muted:    '#6b7280',
          text:     '#f0f0f0',
          subtext:  '#9ca3af',
          grok:     '#7c3aed', // purple for xAI
          gemini:   '#1d6fd8', // blue for Google
          hermes:   '#059669', // green for Together AI
        },
      },
      fontSize: {
        // Large-print mode for 17" MCU screen
        'mcu-sm':   ['18px', '28px'],
        'mcu-base': ['22px', '34px'],
        'mcu-lg':   ['26px', '38px'],
        'mcu-xl':   ['32px', '44px'],
        'mcu-2xl':  ['40px', '52px'],
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
