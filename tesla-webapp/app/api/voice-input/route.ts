/**
 * POST /api/voice-input
 *
 * Accepts voice input from iOS Shortcut (S3XY Button trigger) in two forms:
 *   A) JSON  { text, model?, roomId }          ← iOS "Dictate Text" path (recommended)
 *   B) FormData { audio: File, model?, roomId } ← raw audio → Whisper transcription
 *
 * Flow:
 *   1. Auth via X-Tesla-Key header
 *   2. Extract / transcribe text
 *   3. Publish voice-start to Ably  → Tesla MCU overlay pops up immediately
 *   4. Stream AI (Grok / Gemini)    → publish voice-chunk per token
 *   5. Publish voice-end            → Tesla MCU stops streaming cursor
 *   6. Return { ok, query, model }  → iOS Shortcut gets confirmation
 *
 * The HTTP response is held open until the AI stream finishes so Vercel
 * keeps the serverless function alive throughout (no background tasks needed).
 */

import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'
import { GoogleGenerativeAI } from '@google/generative-ai'
import Ably from 'ably'
import { MODELS } from '@/lib/models'
import type { ModelId } from '@/lib/models'

export const runtime = 'nodejs'
export const maxDuration = 60

// ─── Auth ──────────────────────────────────────────────────────────────────────

function authenticated(req: NextRequest): boolean {
  const secret = process.env.TESLA_VOICE_KEY
  if (!secret) return true // skip auth when env var not set (dev only)
  return req.headers.get('x-tesla-key') === secret
}

// ─── Whisper transcription (optional — only used for raw audio uploads) ────────

async function transcribeAudio(file: File): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY
  if (!apiKey) throw new Error('OPENAI_API_KEY not set; cannot transcribe audio')

  const client = new OpenAI({ apiKey })
  const result = await client.audio.transcriptions.create({
    model: 'whisper-1',
    file,
    language: 'zh', // bilingual zh/en; Whisper auto-detects
  })
  return result.text
}

// ─── AI streaming → Ably publishing ───────────────────────────────────────────

async function streamToAbly(
  query: string,
  model: ModelId,
  roomId: string,
): Promise<void> {
  const config = MODELS[model]
  if (!config) throw new Error(`Unknown model: ${model}`)
  if (!config.apiKey) throw new Error(`API key not configured for ${model}`)

  const ablyRest = new Ably.Rest({ key: process.env.ABLY_API_KEY ?? '' })
  const channel = ablyRest.channels.get(`tesla:${roomId}`)

  // fire-and-forget helper to avoid blocking the stream on Ably round-trips
  const pub = (event: string, data: unknown) =>
    channel.publish(event, data).catch((e) => console.error('[ably]', e))

  // Step 1: signal Tesla MCU to open overlay immediately
  await pub('voice-start', { query, model, ts: Date.now() })

  try {
    if (config.provider === 'openai-compat') {
      // ── Grok (xAI) or Hermes (Together AI) ────────────────────────────────
      const client = new OpenAI({ baseURL: config.baseURL, apiKey: config.apiKey })
      const stream = await client.chat.completions.create({
        model: config.model,
        messages: [{ role: 'user', content: query }],
        stream: true,
      })
      for await (const chunk of stream) {
        const text = chunk.choices[0]?.delta?.content ?? ''
        if (text) pub('voice-chunk', { text, ts: Date.now() })
      }
    } else {
      // ── Gemini ─────────────────────────────────────────────────────────────
      const genai = new GoogleGenerativeAI(config.apiKey)
      const gModel = genai.getGenerativeModel({ model: config.model })
      const result = await gModel.generateContentStream(query)
      for await (const chunk of result.stream) {
        const text = chunk.text()
        if (text) pub('voice-chunk', { text, ts: Date.now() })
      }
    }

    await pub('voice-end', { ts: Date.now() })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'AI stream error'
    await pub('voice-error', { message, ts: Date.now() })
    throw err
  }
}

// ─── Request handler ───────────────────────────────────────────────────────────

export async function POST(req: NextRequest) {
  if (!authenticated(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let query = ''
  let model: ModelId = 'chatgpt'
  let roomId = 'tesla-main'

  const contentType = req.headers.get('content-type') ?? ''

  if (contentType.includes('multipart/form-data')) {
    // ── Path B: raw audio file ───────────────────────────────────────────────
    const form = await req.formData()
    const audioFile = form.get('audio') as File | null
    if (!audioFile) {
      return NextResponse.json({ error: 'Missing audio field in form data' }, { status: 400 })
    }
    model = (form.get('model') as ModelId | null) ?? 'chatgpt'
    roomId = (form.get('roomId') as string | null) ?? 'tesla-main'

    try {
      query = await transcribeAudio(audioFile)
    } catch (err) {
      return NextResponse.json(
        { error: `Transcription failed: ${(err as Error).message}` },
        { status: 500 },
      )
    }
  } else {
    // ── Path A: pre-transcribed text (recommended for iOS Shortcuts) ─────────
    const body = await req.json().catch(() => ({})) as {
      text?: string
      model?: ModelId
      roomId?: string
    }
    query = body.text?.trim() ?? ''
    model = body.model ?? 'chatgpt'
    roomId = body.roomId ?? 'tesla-main'
  }

  if (!query) {
    return NextResponse.json({ error: 'Empty query' }, { status: 400 })
  }

  // Stream to Ably (this keeps the function alive until AI is done)
  try {
    await streamToAbly(query, model, roomId)
    return NextResponse.json({ ok: true, query, model, roomId })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message },
      { status: 500 },
    )
  }
}
