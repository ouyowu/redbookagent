/** @type {import('next').NextConfig} */
const config = {
  experimental: {
    // Allow server-side streaming with longer timeouts for LLM responses.
    serverComponentsExternalPackages: ['ably'],
  },
}

export default config
