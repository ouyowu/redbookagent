/**
 * Multi-model streaming gateway
 * Supports: xAI Grok, Google Gemini, Together AI Hermes
 * Simultaneously streams SSE to caller AND publishes chunks to Ably channel
 * so Tesla MCU and phone stay in real-time sync.
 */
import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'
import { GoogleGenerativeAI } from '@google/generative-ai'
import Ably from 'ably'
import { MODELS } from '@/lib/models'
import type { ModelId } from '@/lib/models'

export const runtime = 'nodejs'
export const maxDuration = 60

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

interface ChatRequest {
  messages: ChatMessage[]
  model?: ModelId
  roomId?: string
}

export async function POST(req: NextRequest) {
  let body: ChatRequest
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const { messages, model = 'chatgpt', roomId = 'default' } = body
  const config = MODELS[model]

  if (!config) {
    return NextResponse.json({ error: `Unknown model: ${model}` }, { status: 400 })
  }
  if (!config.apiKey) {
    return NextResponse.json({ error: `API key not configured for ${model}` }, { status: 503 })
  }

  // Ably REST client — used server-side only for publishing
  const ablyRest = new Ably.Rest({ key: process.env.ABLY_API_KEY ?? '' })
  const channel = ablyRest.channels.get(`tesla:${roomId}`)

  // Fire-and-forget helper — never block the stream on Ably latency
  const pub = (event: string, data: unknown) =>
    channel.publish(event, data).catch((e) => console.error('[ably publish]', e))

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(ctrl) {
      const send = (payload: unknown) =>
        ctrl.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`))

      try {
        // Broadcast stream-start so Tesla MCU creates a new message bubble
        await pub('status', { type: 'start', model, ts: Date.now() })

        if (config.provider === 'openai-compat') {
          // ─── xAI Grok & Together AI Hermes (OpenAI-compatible) ────────────
          const client = new OpenAI({
            baseURL: config.baseURL,
            apiKey: config.apiKey,
          })

          const llmStream = await client.chat.completions.create({
            model: config.model,
            messages,
            stream: true,
          })

          for await (const chunk of llmStream) {
            const text = chunk.choices[0]?.delta?.content ?? ''
            if (!text) continue
            send({ text })
            pub('chunk', { text, ts: Date.now() }) // intentionally not awaited
          }
        } else {
          // ─── Google Gemini ─────────────────────────────────────────────────
          const genai = new GoogleGenerativeAI(config.apiKey)
          const gModel = genai.getGenerativeModel({ model: config.model })

          // Build Gemini chat history from all messages except the last
          const history = messages.slice(0, -1).map((m) => ({
            role: m.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: m.content }],
          }))
          const lastUserMsg = messages[messages.length - 1]?.content ?? ''

          const chat = gModel.startChat({ history })
          const result = await chat.sendMessageStream(lastUserMsg)

          for await (const chunk of result.stream) {
            const text = chunk.text()
            if (!text) continue
            send({ text })
            pub('chunk', { text, ts: Date.now() })
          }
        }

        // Signal completion
        await pub('status', { type: 'end', ts: Date.now() })
        send({ done: true })
        ctrl.close()
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Stream error'
        pub('status', { type: 'error', message, ts: Date.now() })
        send({ error: message })
        ctrl.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // disable Nginx buffering on Vercel
    },
  })
}
