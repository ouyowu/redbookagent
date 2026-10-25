import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tesla Juniper — AI Console',
  description: 'Multi-model AI gateway with real-time Codex sync for Tesla Model Y Juniper MCU',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
  themeColor: '#0d0d0d',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="h-full overflow-hidden">{children}</body>
    </html>
  )
}
