'use client'

import { useEffect, useRef } from 'react'

export interface ToolEvent {
  id: string
  tool: string
  summary: string
  error: boolean
  ts: number
}

export type AgentStatus = 'idle' | 'running'

interface Props {
  events: ToolEvent[]
  status: AgentStatus
}

// ─── Tool metadata ────────────────────────────────────────────────────────────

const TOOL_META: Record<string, { icon: string; color: string; label: string }> = {
  Edit:        { icon: '✏️',  color: '#f59e0b', label: 'Edit'   },
  Write:       { icon: '📝',  color: '#f59e0b', label: 'Write'  },
  Read:        { icon: '📖',  color: '#60a5fa', label: 'Read'   },
  Bash:        { icon: '⚡',  color: '#a78bfa', label: 'Bash'   },
  Agent:       { icon: '🤖',  color: '#34d399', label: 'Agent'  },
  WebFetch:    { icon: '🌐',  color: '#fb923c', label: 'Fetch'  },
  WebSearch:   { icon: '🔍',  color: '#fb923c', label: 'Search' },
  TodoWrite:   { icon: '📋',  color: '#94a3b8', label: 'Todo'   },
}

function meta(tool: string) {
  return TOOL_META[tool] ?? { icon: '🔧', color: '#6b7280', label: tool }
}

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  })
}

// ─── Single event row ─────────────────────────────────────────────────────────

function EventRow({ event, isLatest, status }: {
  event: ToolEvent
  isLatest: boolean
  status: AgentStatus
}) {
  const m = meta(event.tool)
  const isActive = isLatest && status === 'running'

  return (
    <div
      className={[
        'flex items-center gap-4 px-6 py-3 rounded-xl transition-colors',
        isActive
          ? 'bg-tesla-surface border border-tesla-border'
          : 'hover:bg-tesla-surface/50',
      ].join(' ')}
    >
      {/* Timestamp */}
      <span className="text-tesla-muted font-mono text-mcu-sm w-24 shrink-0">
        {formatTime(event.ts)}
      </span>

      {/* Status dot */}
      <span
        className={[
          'w-2.5 h-2.5 rounded-full shrink-0',
          event.error
            ? 'bg-red-500'
            : isActive
              ? 'bg-tesla-accent animate-pulse shadow-[0_0_8px_#e82127]'
              : 'bg-emerald-500',
        ].join(' ')}
      />

      {/* Tool badge */}
      <span
        className="px-3 py-0.5 rounded-lg text-mcu-sm font-bold text-white shrink-0 w-20 text-center"
        style={{ backgroundColor: m.color + '33', color: m.color, border: `1px solid ${m.color}44` }}
      >
        {m.icon} {m.label}
      </span>

      {/* Summary */}
      <span
        className={[
          'font-mono text-mcu-sm truncate flex-1',
          event.error ? 'text-red-400' : isActive ? 'text-tesla-text' : 'text-tesla-subtext',
        ].join(' ')}
      >
        {event.summary || '—'}
      </span>

      {/* Streaming indicator on active row */}
      {isActive && (
        <span className="text-tesla-accent text-mcu-sm shrink-0 animate-pulse">running…</span>
      )}
    </div>
  )
}

// ─── Main component ────────────────────────────────────────────────────────────

export function CodexTerminal({ events, status }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-5 text-tesla-muted">
        <div className="w-20 h-20 rounded-2xl border-2 border-tesla-border flex items-center justify-center text-4xl">
          ⚡
        </div>
        <p className="text-mcu-base">等待 Claude Code 开始工作…</p>
        <p className="text-mcu-sm opacity-60 text-center max-w-md">
          在你的电脑上运行 Claude Code，<br />
          工具调用会实时出现在这里
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto px-4 py-3 space-y-1 font-mono">
      {events.map((ev, i) => (
        <EventRow
          key={ev.id}
          event={ev}
          isLatest={i === events.length - 1}
          status={status}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
