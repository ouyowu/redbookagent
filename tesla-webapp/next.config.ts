import type { NextConfig } from 'next'

const config: NextConfig = {
  experimental: {
    // Allow server-side streaming with longer timeouts for LLM responses
    serverComponentsExternalPackages: ['ably'],
  },
}

export default config
