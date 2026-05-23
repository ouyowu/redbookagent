'use client'

/**
 * Tesla Juniper AI Console — Main Screen
 *
 * Layout (landscape, 17" MCU):
 *   ┌──────────────────────┬──────────────────────────┐
 *   │   ChatPanel (45%)    │   CodexMonitor (55%)     │
 *   │  model selector      │  real-time Ably stream   │
 *   │  chat history        │  syntax-highlighted code │
 *   │  input box           │  streaming status        │
 *   └──────────────────────┴──────────────────────────┘
 *
 * Both panels share the same roomId and Ably channel via useAblyChannel.
 * Phone users can open the same URL with ?room=<id> to sync in real-time.
 */

import { useMemo, useState } from 'react'
import { ChatPanel } from '@/components/ChatPanel'
import { CodexMonitor } from '@/components/CodexMonitor'
import { VoiceOverlay } from '@/components/VoiceOverlay'
import { useAblyChannel } from '@/hooks/useAblyChannel'
import type { ModelId } from '@/lib/models'

function getRoomId(): string {
  if (typeof window === 'undefined') return 'tesla-main'
  const params = new URLSearchParams(window.location.search)
  return params.get('room') ?? process.env.NEXT_PUBLIC_DEFAULT_ROOM ?? 'tesla-main'
}

function getClientId(): string {
  if (typeof window === 'undefined') return 'ssr'
  let id = sessionStorage.getItem('tesla_client_id')
  if (!id) {
    id = `client-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    sessionStorage.setItem('tesla_client_id', id)
  }
  return id
}

export default function TeslaConsole() {
  const roomId = useMemo(getRoomId, [])
  const clientId = useMemo(getClientId, [])

  const {
    messages,
    connectionState,
    activeModel,
    voiceState,
    broadcastModelSwitch,
    clearMessages,
    dismissVoice,
  } = useAblyChannel(roomId, clientId)

  const [localModel, setLocalModel] = useState<ModelId>(activeModel)

  const handleModelChange = (model: ModelId) => {
    setLocalModel(model)
    broadcastModelSwitch(model) // syncs to Tesla MCU if changed from phone
  }

  return (
    <main className="h-full flex flex-col bg-tesla-bg">
      {/* ── Status bar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-2 bg-tesla-surface border-b border-tesla-border shrink-0">
        <div className="flex items-center gap-2">
          {/* Tesla "T" wordmark */}
          <span className="text-tesla-accent font-bold text-mcu-lg tracking-wider">T</span>
          <span className="text-tesla-text text-mcu-base font-semibold">Model Y Juniper</span>
          <span className="text-tesla-muted text-mcu-sm">AI Console</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-tesla-muted text-mcu-sm">
            Room: <code className="text-tesla-subtext">{roomId}</code>
          </span>
          <span
            className={[
              'flex items-center gap-1.5 text-mcu-sm',
              connectionState === 'connected' ? 'text-emerald-400' : 'text-tesla-muted',
            ].join(' ')}
          >
            <span
              className={[
                'w-2 h-2 rounded-full',
                connectionState === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_6px_#34d399]'
                  : connectionState === 'connecting'
                    ? 'bg-yellow-400 animate-pulse'
                    : 'bg-tesla-muted',
              ].join(' ')}
            />
            {connectionState}
          </span>
        </div>
      </div>

      {/* ── Two-column layout ──────────────────────────────────────────────── */}
      <div className="flex-1 grid grid-cols-[45fr_55fr] min-h-0">
        <ChatPanel
          roomId={roomId}
          activeModel={localModel}
          onModelChange={handleModelChange}
        />
        <CodexMonitor
          messages={messages}
          isConnected={connectionState === 'connected'}
          onClear={clearMessages}
        />
      </div>

      {/* ── Voice overlay: pops up when S3XY Button triggers iOS Shortcut ── */}
      <VoiceOverlay state={voiceState} onDismiss={dismissVoice} />
    </main>
  )
}
