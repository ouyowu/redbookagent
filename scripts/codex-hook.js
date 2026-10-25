#!/usr/bin/env node
/**
 * Claude Code PostToolUse hook → Ably publisher
 *
 * 每次 Claude Code 调用工具后自动触发，把工具调用信息推送到 Ably，
 * Tesla MCU 的 /codex 页面实时显示。
 *
 * 安装步骤：
 *   1. 把这个文件放到任意固定路径，例如 ~/scripts/codex-hook.js
 *   2. 在 ~/.claude/settings.json 里添加 hooks 配置（见下方注释）
 *   3. 设置环境变量：export ABLY_API_KEY=xxxxx.yyyyy:zzzzz
 *      export TESLA_ROOM_ID=tesla-main（可选，默认 tesla-main）
 *
 * ~/.claude/settings.json 配置：
 * {
 *   "hooks": {
 *     "PostToolUse": [{
 *       "matcher": ".*",
 *       "hooks": [{ "type": "command", "command": "node ~/scripts/codex-hook.js" }]
 *     }],
 *     "Stop": [{
 *       "matcher": ".*",
 *       "hooks": [{ "type": "command", "command": "CODEX_STOP=1 node ~/scripts/codex-hook.js" }]
 *     }]
 *   }
 * }
 */

'use strict'

const https = require('https')
const path  = require('path')

const ABLY_KEY = process.env.ABLY_API_KEY
const ROOM_ID  = process.env.TESLA_ROOM_ID || 'tesla-main'
const IS_STOP  = process.env.CODEX_STOP === '1'

if (!ABLY_KEY) {
  // Silent exit — don't break Claude Code if env var is missing
  process.exit(0)
}

// ─── Tool input → human-readable summary ──────────────────────────────────────

function summarize(toolName, input) {
  if (!input) return ''
  try {
    switch (toolName) {
      case 'Edit':
      case 'Write':
        return relative(input.file_path)
      case 'Read':
        return relative(input.file_path) + (input.limit ? ` (${input.limit} lines)` : '')
      case 'Bash':
        return String(input.command || '').replace(/\n/g, ' ').slice(0, 90)
      case 'Agent':
        return String(input.description || input.prompt || '').slice(0, 80)
      case 'WebFetch':
        return String(input.url || '').slice(0, 80)
      case 'WebSearch':
        return String(input.query || '').slice(0, 80)
      case 'TodoWrite':
        return `${(input.todos || []).length} todos`
      default:
        return JSON.stringify(input).slice(0, 80)
    }
  } catch {
    return ''
  }
}

function relative(filePath) {
  if (!filePath) return '?'
  try {
    return path.relative(process.cwd(), filePath)
  } catch {
    return filePath
  }
}

// ─── Ably REST publish (no SDK — just built-in https) ────────────────────────

function publish(eventName, data) {
  return new Promise((resolve) => {
    const body = JSON.stringify([{ name: eventName, data }])
    const channel = `tesla:${ROOM_ID}`
    const auth = Buffer.from(ABLY_KEY).toString('base64')

    const req = https.request(
      {
        hostname: 'rest.ably.io',
        path: `/channels/${encodeURIComponent(channel)}/messages`,
        method: 'POST',
        headers: {
          Authorization:   `Basic ${auth}`,
          'Content-Type':  'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        timeout: 4000,
      },
      (res) => {
        res.resume() // drain response
        res.on('end', resolve)
      },
    )
    req.on('error', resolve)  // never throw — don't block Claude Code
    req.on('timeout', () => { req.destroy(); resolve() })
    req.write(body)
    req.end()
  })
}

// ─── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  if (IS_STOP) {
    await publish('codex:status', { status: 'idle', ts: Date.now() })
    return
  }

  // Claude Code passes hook data as JSON on stdin
  let raw = ''
  for await (const chunk of process.stdin) raw += chunk

  let hook
  try { hook = JSON.parse(raw) } catch { return }

  const toolName = hook.tool_name || hook.toolName || 'Unknown'
  const toolInput = hook.tool_input || hook.toolInput || {}
  const isError = !!(hook.tool_response?.error || hook.error)

  await publish('codex:tool', {
    tool:    toolName,
    summary: summarize(toolName, toolInput),
    error:   isError,
    ts:      Date.now(),
  })
}

main().catch(() => {}) // never crash Claude Code
