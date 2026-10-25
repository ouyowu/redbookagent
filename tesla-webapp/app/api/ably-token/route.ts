/**
 * Ably token request endpoint.
 * Clients never see the ABLY_API_KEY; they request a short-lived token here.
 * Each token is scoped to the client's roomId channel only.
 */
import Ably from 'ably'
import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  const { clientId, roomId = 'default' } = await req.json().catch(() => ({}))

  if (!process.env.ABLY_API_KEY) {
    return NextResponse.json({ error: 'ABLY_API_KEY not configured' }, { status: 503 })
  }

  const ably = new Ably.Rest({ key: process.env.ABLY_API_KEY })

  const tokenRequest = await ably.auth.createTokenRequest({
    clientId: clientId ?? `anon-${Date.now()}`,
    ttl: 3600_000, // 1 hour
    capability: {
      // Scope to the specific room channel only
      [`tesla:${roomId}`]: ['subscribe', 'publish', 'presence'],
    },
  })

  return NextResponse.json(tokenRequest)
}
