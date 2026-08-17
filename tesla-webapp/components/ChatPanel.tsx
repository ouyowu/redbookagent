'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ModelSelector } from './ModelSelector'
import type { ModelId } from '@/lib/models'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  roomId: string
}

export function ChatPanel({ roomId }: Props) {
  const activeModel: ModelId = 'gemini'
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = useCallback(async () => {
    const text = input.trim()
    if (!text || isStreaming) return

    const newMessages: Message[] = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)
    setInput('')
    setIsStreaming(true)

    // Placeholder for the assistant reply that will be filled by streaming
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    abortRef.current = new AbortController()

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages, model: activeModel, roomId }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const dec = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buf += dec.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (!payload) continue

          const data = JSON.parse(payload) as { text?: string; done?: boolean; error?: string }

          if (data.error) throw new Error(data.error)
          if (data.done) break

          if (data.text) {
            setMessages((prev) => {
              const copy = [...prev]
              copy[copy.length - 1] = {
                role: 'assistant',
                content: copy[copy.length - 1].content + data.text,
              }
              return copy
            })
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setMessages((prev) => {
        const copy = [...prev]
        copy[copy.length - 1] = {
          role: 'assistant',
          content: `⚠ ${(err as Error).message}`,
        }
        return copy
      })
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [input, isStreaming, messages, activeModel, roomId])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter submits
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <section className="flex flex-col h-full bg-tesla-bg border-r border-tesla-border">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-tesla-border shrink-0">
        <span className="text-tesla-text text-mcu-lg font-bold">Chat</span>
        <ModelSelector />
      </div>

      {/* Message history */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
        {messages.length === 0 && (
          <p className="text-tesla-muted text-mcu-base text-center mt-16">
            开始对话 ↓
          </p>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={[
                'max-w-[85%] px-5 py-3 rounded-2xl text-mcu-base leading-relaxed whitespace-pre-wrap break-words',
                m.role === 'user'
                  ? 'bg-tesla-accent text-white rounded-br-sm'
                  : 'bg-tesla-surface text-tesla-text border border-tesla-border rounded-bl-sm',
              ].join(' ')}
            >
              {m.content}
              {m.role === 'assistant' && isStreaming && i === messages.length - 1 && (
                <span className="inline-block w-2.5 h-5 bg-tesla-text animate-pulse rounded-sm ml-1 align-middle" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="px-6 py-4 border-t border-tesla-border shrink-0">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息… (Ctrl+Enter 发送)"
            rows={3}
            className={[
              'flex-1 bg-tesla-surface border border-tesla-border rounded-xl',
              'text-tesla-text text-mcu-base placeholder:text-tesla-muted',
              'px-4 py-3 outline-none resize-none',
              'focus:border-tesla-accent transition-colors',
            ].join(' ')}
          />
          <button
            onClick={handleSubmit}
            disabled={isStreaming || !input.trim()}
            className={[
              'h-14 w-14 rounded-xl flex items-center justify-center text-2xl',
              'transition-all duration-150',
              isStreaming || !input.trim()
                ? 'bg-tesla-surface text-tesla-muted cursor-not-allowed'
                : 'bg-tesla-accent text-white hover:opacity-90 active:scale-95',
            ].join(' ')}
          >
            {isStreaming ? '…' : '↑'}
          </button>
        </div>

        <p className="text-tesla-muted text-mcu-sm mt-2 text-right">
          Room: <span className="text-tesla-subtext font-mono">{roomId}</span>
        </p>
      </div>
    </section>
  )
}
