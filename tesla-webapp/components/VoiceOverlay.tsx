'use client'

/**
 * VoiceOverlay — full-screen Tesla MCU popup for S3XY Button voice queries
 *
 * Triggered when the Ably channel receives a 'voice-start' event.
 * Shows the user's spoken query at the top, then streams the AI response
 * with a typewriter cursor effect and live syntax-highlighted code blocks.
 *
 * Dismiss: tap anywhere on the overlay, or it auto-dismisses 12s after
 * the AI finishes streaming.
 */

import { useEffect, useRef, useCallback } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { MODEL_META } from '@/lib/models'
import type { ModelId } from '@/lib/models'

// ─── Types ──────────────────────────────────────────────────────────────────────

export interface VoiceState {
  query: string
  model: ModelId
  response: string
  isStreaming: boolean
  isError: boolean
  ts: number
}

interface Props {
  state: VoiceState | null
  onDismiss: () => void
}

// ─── Code-block parser (same as CodexMonitor) ──────────────────────────────────

interface TextSeg { kind: 'text'; content: string }
interface CodeSeg { kind: 'code'; lang: string; content: string }
type Segment = TextSeg | CodeSeg

function parseSegments(raw: string): Segment[] {
  const segs: Segment[] = []
  const re = /```(\w*)\n?([\s\S]*?)```/g
  let last = 0
  let m: RegExpExecArray | null

  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) segs.push({ kind: 'text', content: raw.slice(last, m.index) })
    segs.push({ kind: 'code', lang: m[1] || 'plaintext', content: m[2] })
    last = m.index + m[0].length
  }

  const tail = raw.slice(last)
  if (tail) {
    const open = tail.match(/^```(\w*)[\n]?([\s\S]*)/)
    open
      ? segs.push({ kind: 'code', lang: open[1] || 'plaintext', content: open[2] })
      : segs.push({ kind: 'text', content: tail })
  }

  return segs
}

// ─── Pulsing waveform animation (shows while streaming) ───────────────────────

function VoiceWave({ active }: { active: boolean }) {
  return (
    <div className="flex items-end gap-[3px] h-8" aria-hidden>
      {[0.4, 0.7, 1, 0.7, 0.5, 0.9, 0.6].map((h, i) => (
        <span
          key={i}
          className={[
            'w-1 rounded-full bg-tesla-accent transition-all',
            active ? 'animate-pulse' : 'opacity-30',
          ].join(' ')}
          style={{
            height: `${Math.round(h * 100)}%`,
            animationDelay: `${i * 80}ms`,
          }}
        />
      ))}
    </div>
  )
}

// ─── Main component ────────────────────────────────────────────────────────────

export function VoiceOverlay({ state, onDismiss }: Props) {
  const autoDismissRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const responseRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom as text streams in
  useEffect(() => {
    responseRef.current?.scrollTo({ top: responseRef.current.scrollHeight, behavior: 'smooth' })
  }, [state?.response])

  // Auto-dismiss 12 seconds after streaming completes
  useEffect(() => {
    if (state && !state.isStreaming && !state.isError) {
      autoDismissRef.current = setTimeout(onDismiss, 12_000)
    }
    return () => {
      if (autoDismissRef.current) clearTimeout(autoDismissRef.current)
    }
  }, [state?.isStreaming, state?.isError, onDismiss])

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      // Only dismiss on click directly on the backdrop, not on content
      if (e.target === e.currentTarget) onDismiss()
    },
    [onDismiss],
  )

  if (!state) return null

  const meta = MODEL_META[state.model] ?? MODEL_META.grok
  const segments = parseSegments(state.response)

  return (
    /* ── Backdrop ──────────────────────────────────────────────────────────── */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm"
      style={{ animation: 'fadeIn 200ms ease-out' }}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-label="AI Voice Response"
    >
      {/* ── Card ─────────────────────────────────────────────────────────────── */}
      <div
        className="relative w-[92vw] max-h-[88vh] flex flex-col bg-tesla-surface rounded-3xl border border-tesla-border overflow-hidden"
        style={{ animation: 'slideUp 250ms cubic-bezier(0.16, 1, 0.3, 1)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header: query + model badge ──────────────────────────────────── */}
        <div className="flex items-start gap-4 px-8 py-5 border-b border-tesla-border shrink-0">
          {/* Mic icon */}
          <div className="mt-1 shrink-0 w-10 h-10 rounded-xl bg-tesla-accent/20 border border-tesla-accent/40 flex items-center justify-center">
            <svg className="w-5 h-5 text-tesla-accent" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4Z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v4M8 23h8"/>
            </svg>
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-tesla-muted text-mcu-sm mb-1">你问了：</p>
            <p className="text-tesla-text text-mcu-lg font-semibold leading-snug break-words">
              {state.query}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Model badge */}
            <span
              className="px-4 py-1.5 rounded-full text-mcu-sm font-bold text-white"
              style={{ backgroundColor: meta.badgeColor }}
            >
              {meta.badge}
            </span>

            {/* Dismiss button */}
            <button
              onClick={onDismiss}
              className="w-10 h-10 rounded-full bg-tesla-border hover:bg-tesla-muted/40 flex items-center justify-center text-tesla-subtext text-xl transition-colors"
              aria-label="关闭"
            >
              ✕
            </button>
          </div>
        </div>

        {/* ── Streaming response ─────────────────────────────────────────────── */}
        <div
          ref={responseRef}
          className="flex-1 overflow-y-auto px-8 py-6 space-y-2"
        >
          {state.isError ? (
            <p className="text-red-400 text-mcu-base">⚠ {state.response || '请求失败，请重试'}</p>
          ) : segments.length === 0 && state.isStreaming ? (
            /* Initial blank state: show pulsing cursor while waiting for first chunk */
            <div className="flex items-center gap-3 mt-8">
              <span className="w-4 h-8 bg-tesla-accent rounded-sm animate-pulse" />
              <span className="text-tesla-muted text-mcu-base">{meta.label} 正在思考…</span>
            </div>
          ) : (
            segments.map((seg, i) =>
              seg.kind === 'code' ? (
                <SyntaxHighlighter
                  key={i}
                  language={seg.lang}
                  style={vscDarkPlus}
                  customStyle={{
                    margin: '12px 0',
                    borderRadius: '16px',
                    fontSize: '20px',
                    lineHeight: '1.65',
                    background: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                  }}
                  showLineNumbers={seg.content.split('\n').length > 4}
                >
                  {seg.content}
                </SyntaxHighlighter>
              ) : (
                <p
                  key={i}
                  className="text-tesla-text text-mcu-base leading-relaxed whitespace-pre-wrap"
                >
                  {seg.content}
                  {/* Typewriter cursor on last text segment during streaming */}
                  {i === segments.length - 1 && state.isStreaming && (
                    <span className="inline-block w-3 h-7 bg-tesla-accent rounded-sm ml-1 align-middle animate-pulse" />
                  )}
                </p>
              ),
            )
          )}
        </div>

        {/* ── Footer: status bar ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-8 py-3 border-t border-tesla-border bg-tesla-bg/60 shrink-0">
          <div className="flex items-center gap-4">
            <VoiceWave active={state.isStreaming} />
            <span className={`text-mcu-sm ${state.isStreaming ? 'text-tesla-accent' : 'text-tesla-muted'}`}>
              {state.isStreaming ? `${meta.label} 正在生成…` : `${meta.label} 已完成`}
            </span>
          </div>

          {!state.isStreaming && !state.isError && (
            <span className="text-tesla-muted text-mcu-sm animate-pulse">
              轻触背景关闭 · 12秒后自动关闭
            </span>
          )}
        </div>
      </div>

      {/* Inline keyframe styles (Tailwind can't generate dynamic keyframes) */}
      <style>{`
        @keyframes fadeIn  { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(40px) scale(0.97) }
                             to   { opacity: 1; transform: translateY(0)     scale(1)    } }
      `}</style>
    </div>
  )
}
