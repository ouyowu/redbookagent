'use client'

/**
 * /codex — Tesla MCU 只读 Codex 监控页
 *
 * 车机浏览器收藏这个 URL：
 *   https://your-app.vercel.app/codex?room=tesla-main
 *
 * 电脑端运行 scripts/codex-hook.js（Claude Code PostToolUse 钩子），
 * 每次工具调用就会在这里实时出现一行。
 */

import { useMemo, useEffect, useRef, useState } from 'react'
import { CodexTerminal } from '@/components/CodexTerminal'
import type { ToolEvent, AgentStatus } from '@/components/CodexTerminal'
import type { ConnectionState } from '@/hooks/useAblyChannel'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getRoomId(): string {
  if (typeof window === 'undefined') return 'tesla-main'
  return new URLSearchParams(window.location.search).get('room')
    ?? process.env.NEXT_PUBLIC_DEFAULT_ROOM
    ?? 'tesla-main'
}

function getClientId(): string {
  if (typeof window === 'undefined') return 'ssr'
  let id = sessionStorage.getItem('tesla_codex_id')
  if (!id) {
    id = `codex-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    sessionStorage.setItem('tesla_codex_id', id)
  }
  return id
}

function elapsed(startTs: number): string {
  const s = Math.floor((Date.now() - startTs) / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  return `${m}m ${s % 60}s`
}

// ─── Ably connection (inline, no shared hook needed for this read-only page) ──

function useCodexFeed(roomId: string, clientId: string) {
  const [events, setEvents]           = useState<ToolEvent[]>([])
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle')
  const [connState, setConnState]     = useState<ConnectionState>('connecting')
  const [startTs, setStartTs]         = useState<number | null>(null)
  const [actionCount, setActionCount] = useState(0)
  const ablyRef = useRef<import('ably').Realtime | null>(null)

  useEffect(() => {
    let alive = true

    async function connect() {
      const { default: Ably } = await import('ably')

      const client = new Ably.Realtime({
        authUrl: '/api/ably-token',
        authMethod: 'POST',
        authParams: { clientId, roomId },
        clientId,
        recover: (_, cb) => cb(true),
      })
      ablyRef.current = client

      const stateMap: Record<string, ConnectionState> = {
        connected: 'connected', disconnected: 'disconnected',
        suspended: 'suspended', connecting: 'connecting', initialized: 'connecting',
      }
      client.connection.on((s) => {
        if (alive) setConnState(stateMap[s.current] ?? 'disconnected')
      })

      const channel = client.channels.get(`tesla:${roomId}`)

      // ── tool event ────────────────────────────────────────────────────────
      channel.subscribe('codex:tool', (msg) => {
        if (!alive) return
        const d = msg.data as { tool: string; summary: string; error: boolean; ts: number }
        const ev: ToolEvent = {
          id:      `ev-${d.ts}-${Math.random().toString(36).slice(2, 5)}`,
          tool:    d.tool,
          summary: d.summary,
          error:   d.error,
          ts:      d.ts,
        }
        setEvents((prev) => [...prev.slice(-199), ev]) // keep last 200
        setAgentStatus('running')
        setActionCount((n) => n + 1)
        setStartTs((prev) => prev ?? d.ts)
      })

      // ── status event (Stop hook sets idle) ────────────────────────────────
      channel.subscribe('codex:status', (msg) => {
        if (!alive) return
        const d = msg.data as { status: AgentStatus }
        setAgentStatus(d.status)
        if (d.status === 'idle') {
          setStartTs(null)
          setActionCount(0)
        }
      })
    }

    connect().catch(console.error)

    return () => {
      alive = false
      ablyRef.current?.close()
    }
  }, [roomId, clientId])

  return { events, agentStatus, connState, startTs, actionCount }
}

// ─── Stats card ───────────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center px-6 py-3 bg-tesla-surface rounded-2xl border border-tesla-border">
      <span className="text-tesla-muted text-mcu-sm">{label}</span>
      <span className="text-tesla-text text-mcu-xl font-bold font-mono">{value}</span>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function CodexPage() {
  const roomId   = useMemo(getRoomId, [])
  const clientId = useMemo(getClientId, [])
  const { events, agentStatus, connState, startTs, actionCount } =
    useCodexFeed(roomId, clientId)

  // Live elapsed ticker
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const lastTool = events[events.length - 1]?.tool ?? '—'

  return (
    <main className="h-full flex flex-col bg-tesla-bg">

      {/* ── Top bar ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 bg-tesla-surface border-b border-tesla-border shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-tesla-accent font-bold text-mcu-lg">T</span>
          <span className="text-tesla-text text-mcu-base font-semibold">Codex Monitor</span>
          <span className="text-tesla-muted text-mcu-sm">只读 · 实时同步</span>
        </div>

        <div className="flex items-center gap-5">
          <span className="text-tesla-muted text-mcu-sm font-mono">
            room: <span className="text-tesla-subtext">{roomId}</span>
          </span>

          <a
            href="/"
            className="text-tesla-muted text-mcu-sm hover:text-tesla-text transition-colors border border-tesla-border px-3 py-1 rounded-lg"
          >
            ← Chat
          </a>

          {/* Connection dot */}
          <div className="flex items-center gap-2">
            <span
              className={[
                'w-2.5 h-2.5 rounded-full',
                connState === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_6px_#34d399]'
                  : connState === 'connecting'
                    ? 'bg-yellow-400 animate-pulse'
                    : 'bg-tesla-muted',
              ].join(' ')}
            />
            <span
              className={`text-mcu-sm ${connState === 'connected' ? 'text-emerald-400' : 'text-tesla-muted'}`}
            >
              {connState}
            </span>
          </div>
        </div>
      </div>

      {/* ── Stats row ───────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 px-6 py-4 shrink-0 border-b border-tesla-border">
        {/* Agent status pill */}
        <div
          className={[
            'flex items-center gap-2 px-5 py-2 rounded-2xl border text-mcu-base font-semibold',
            agentStatus === 'running'
              ? 'border-tesla-accent/50 bg-tesla-accent/10 text-tesla-accent'
              : 'border-tesla-border bg-tesla-surface text-tesla-muted',
          ].join(' ')}
        >
          <span
            className={[
              'w-2.5 h-2.5 rounded-full',
              agentStatus === 'running' ? 'bg-tesla-accent animate-pulse' : 'bg-tesla-muted',
            ].join(' ')}
          />
          {agentStatus === 'running' ? '▶ 工作中' : '● 空闲'}
        </div>

        <StatCard label="操作数" value={String(actionCount)} />
        <StatCard
          label="耗时"
          value={startTs ? elapsed(startTs) : '—'}
        />
        <StatCard label="最近工具" value={lastTool} />

        {/* Spacer */}
        <div className="flex-1" />

        {events.length > 0 && (
          <button
            onClick={() => {
              // Clear only local display — does not affect hook
              window.location.reload()
            }}
            className="text-tesla-muted text-mcu-sm border border-tesla-border px-4 py-2 rounded-xl hover:border-tesla-muted transition-colors"
          >
            清空
          </button>
        )}
      </div>

      {/* ── Terminal feed ───────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0">
        <CodexTerminal events={events} status={agentStatus} />
      </div>
    </main>
  )
}
