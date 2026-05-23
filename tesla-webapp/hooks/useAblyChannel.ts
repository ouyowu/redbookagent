'use client'

/**
 * useAblyChannel — core real-time sync hook
 *
 * Both Tesla MCU and phone call this hook with the same roomId.
 * When the phone triggers a chat request, the server publishes chunks
 * to the Ably channel; Tesla MCU receives them here in real-time.
 *
 * Event protocol on channel `tesla:{roomId}`:
 *   status  { type: 'start' | 'end' | 'error', model?, message?, ts }
 *   chunk   { text: string, ts: number }
 *   switch  { model: ModelId, ts: number }   — model changed by other device
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import type { ModelId } from '@/lib/models'

// ─── Message types ─────────────────────────────────────────────────────────────

export interface CodexMessage {
  id: string
  model: ModelId
  text: string
  isStreaming: boolean
  isError: boolean
  ts: number
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'suspended'

export interface AblyChannelResult {
  messages: CodexMessage[]
  connectionState: ConnectionState
  activeModel: ModelId
  /** Publish a model-switch event so the other device sees the change */
  broadcastModelSwitch: (model: ModelId) => void
  clearMessages: () => void
}

// ─── Hook ──────────────────────────────────────────────────────────────────────

export function useAblyChannel(
  roomId: string,
  clientId: string,
  initialModel: ModelId = 'grok',
): AblyChannelResult {
  const [messages, setMessages] = useState<CodexMessage[]>([])
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [activeModel, setActiveModel] = useState<ModelId>(initialModel)

  // Refs keep closure-stable references without causing re-renders
  const ablyRef = useRef<import('ably').Realtime | null>(null)
  const channelRef = useRef<import('ably').RealtimeChannel | null>(null)
  const pendingMsgIdRef = useRef<string | null>(null)

  useEffect(() => {
    let alive = true

    async function connect() {
      // Dynamic import keeps Ably out of the SSR bundle
      const { default: Ably } = await import('ably')

      const client = new Ably.Realtime({
        authUrl: '/api/ably-token',
        authMethod: 'POST',
        authParams: { clientId, roomId },
        clientId,
        // Recover state on reconnect so no messages are missed
        recover: (_, cb) => cb(true),
      })

      ablyRef.current = client

      client.connection.on((stateChange) => {
        if (!alive) return
        const map: Record<string, ConnectionState> = {
          connected: 'connected',
          disconnected: 'disconnected',
          suspended: 'suspended',
          connecting: 'connecting',
          initialized: 'connecting',
        }
        setConnectionState(map[stateChange.current] ?? 'disconnected')
      })

      const channel = client.channels.get(`tesla:${roomId}`)
      channelRef.current = channel

      // ── status events ────────────────────────────────────────────────────
      channel.subscribe('status', (msg) => {
        if (!alive) return
        const data = msg.data as { type: string; model?: ModelId; message?: string; ts: number }

        if (data.type === 'start') {
          const id = `msg-${data.ts}-${Math.random().toString(36).slice(2, 6)}`
          pendingMsgIdRef.current = id
          if (data.model) setActiveModel(data.model)
          setMessages((prev) => [
            ...prev,
            {
              id,
              model: data.model ?? initialModel,
              text: '',
              isStreaming: true,
              isError: false,
              ts: data.ts,
            },
          ])
        }

        if (data.type === 'end') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingMsgIdRef.current ? { ...m, isStreaming: false } : m,
            ),
          )
          pendingMsgIdRef.current = null
        }

        if (data.type === 'error') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingMsgIdRef.current
                ? { ...m, isStreaming: false, isError: true, text: m.text || (data.message ?? 'Error') }
                : m,
            ),
          )
          pendingMsgIdRef.current = null
        }
      })

      // ── chunk events ─────────────────────────────────────────────────────
      channel.subscribe('chunk', (msg) => {
        if (!alive || !pendingMsgIdRef.current) return
        const { text } = msg.data as { text: string; ts: number }
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingMsgIdRef.current ? { ...m, text: m.text + text } : m,
          ),
        )
      })

      // ── model-switch events (from other device) ───────────────────────────
      channel.subscribe('switch', (msg) => {
        if (!alive) return
        const { model } = msg.data as { model: ModelId }
        if (model) setActiveModel(model)
      })
    }

    connect().catch(console.error)

    return () => {
      alive = false
      channelRef.current?.unsubscribe()
      ablyRef.current?.close()
    }
  }, [roomId, clientId, initialModel])

  const broadcastModelSwitch = useCallback((model: ModelId) => {
    setActiveModel(model)
    channelRef.current
      ?.publish('switch', { model, ts: Date.now() })
      .catch(console.error)
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, connectionState, activeModel, broadcastModelSwitch, clearMessages }
}
