'use client'

/**
 * CodexMonitor — Tesla MCU real-time output panel
 *
 * Subscribes to the Ably channel and renders AI responses as they stream in.
 * Code fences (```lang ... ```) are syntax-highlighted automatically.
 */

import { useEffect, useRef } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { CodexMessage } from '@/hooks/useAblyChannel'
import type { ModelId } from '@/lib/models'
import { MODEL_META } from '@/lib/models'

// ─── Markdown-ish code block parser ────────────────────────────────────────────

interface TextSegment { kind: 'text'; content: string }
interface CodeSegment { kind: 'code'; lang: string; content: string }
type Segment = TextSegment | CodeSegment

function parseSegments(raw: string): Segment[] {
  const segments: Segment[] = []
  const fenceRe = /```(\w*)\n?([\s\S]*?)```/g
  let last = 0
  let match: RegExpExecArray | null

  while ((match = fenceRe.exec(raw)) !== null) {
    if (match.index > last) {
      segments.push({ kind: 'text', content: raw.slice(last, match.index) })
    }
    segments.push({ kind: 'code', lang: match[1] || 'plaintext', content: match[2] })
    last = match.index + match[0].length
  }

  // Tail text (may include unclosed fence during streaming)
  if (last < raw.length) {
    const tail = raw.slice(last)
    const openFence = tail.match(/^```(\w*)[\n]?([\s\S]*)/)
    if (openFence) {
      // Streaming: unclosed code block — render as partial code
      segments.push({ kind: 'code', lang: openFence[1] || 'plaintext', content: openFence[2] })
    } else {
      segments.push({ kind: 'text', content: tail })
    }
  }

  return segments
}

// ─── Single message bubble ─────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: CodexMessage }) {
  const meta = MODEL_META[msg.model as ModelId] ?? MODEL_META.chatgpt
  const segments = parseSegments(msg.text)

  return (
    <article className="mb-6">
      {/* Header row */}
      <div className="flex items-center gap-3 mb-2">
        <span
          className="px-3 py-0.5 rounded-full text-mcu-sm font-semibold text-white"
          style={{ backgroundColor: meta.badgeColor }}
        >
          {meta.badge}
        </span>
        <span className="text-tesla-subtext text-mcu-sm">{meta.label}</span>
        {msg.isStreaming && (
          <span className="flex items-center gap-1 text-tesla-accent text-mcu-sm">
            <span className="w-2 h-2 rounded-full bg-tesla-accent animate-pulse inline-block" />
            streaming
          </span>
        )}
        {msg.isError && (
          <span className="text-red-400 text-mcu-sm">⚠ error</span>
        )}
        <span className="ml-auto text-tesla-muted text-mcu-sm">
          {new Date(msg.ts).toLocaleTimeString()}
        </span>
      </div>

      {/* Content */}
      <div
        className={[
          'rounded-2xl p-4 border',
          msg.isError
            ? 'border-red-800 bg-red-950/30'
            : 'border-tesla-border bg-tesla-surface',
        ].join(' ')}
      >
        {segments.length === 0 && msg.isStreaming && (
          <span className="inline-block w-3 h-6 bg-tesla-text animate-pulse rounded-sm" />
        )}

        {segments.map((seg, i) =>
          seg.kind === 'code' ? (
            <SyntaxHighlighter
              key={i}
              language={seg.lang}
              style={vscDarkPlus}
              customStyle={{
                margin: '8px 0',
                borderRadius: '12px',
                fontSize: '18px',
                lineHeight: '1.6',
                background: '#0a0a0a',
              }}
              showLineNumbers={seg.content.split('\n').length > 5}
            >
              {seg.content}
            </SyntaxHighlighter>
          ) : (
            <p
              key={i}
              className="text-tesla-text text-mcu-base leading-relaxed whitespace-pre-wrap"
            >
              {seg.content}
              {i === segments.length - 1 && msg.isStreaming && (
                <span className="inline-block w-2.5 h-5 bg-tesla-text animate-pulse rounded-sm ml-1 align-middle" />
              )}
            </p>
          ),
        )}
      </div>
    </article>
  )
}

// ─── Main panel ───────────────────────────────────────────────────────────────

interface Props {
  messages: CodexMessage[]
  isConnected: boolean
  onClear: () => void
}

export function CodexMonitor({ messages, isConnected, onClear }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <section className="flex flex-col h-full bg-tesla-bg">
      {/* Panel header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-tesla-border shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-tesla-text text-mcu-lg font-bold">Codex Monitor</span>
          <span
            className={[
              'w-3 h-3 rounded-full',
              isConnected ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-tesla-muted',
            ].join(' ')}
          />
          <span className={`text-mcu-sm ${isConnected ? 'text-emerald-400' : 'text-tesla-muted'}`}>
            {isConnected ? 'live' : 'offline'}
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={onClear}
            className="text-tesla-muted text-mcu-sm hover:text-tesla-text transition-colors px-3 py-1 rounded-lg border border-tesla-border hover:border-tesla-muted"
          >
            Clear
          </button>
        )}
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-1 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-tesla-muted">
            <div className="w-16 h-16 rounded-2xl border-2 border-tesla-border flex items-center justify-center">
              <span className="text-3xl">⚡</span>
            </div>
            <p className="text-mcu-base">等待来自手机端的 Codex 输出…</p>
            <p className="text-mcu-sm opacity-60">在同一个 Room ID 下操作，车机将实时同步</p>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  )
}
