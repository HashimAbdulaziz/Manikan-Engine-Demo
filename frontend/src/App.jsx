import { Routes, Route } from 'react-router-dom'
import StorePage from './pages/StorePage'
import ProductDetailPage from './pages/ProductDetailPage'

/* ── Original Engine imports (preserved for /engine route) ─────────────── */
import { useState, useCallback, useRef } from 'react'
import ControlPanel from './components/ControlPanel'
import AvatarViewer from './components/AvatarViewer'

const API_URL = 'http://localhost:8000/generate-avatar'

/* ─────────────────────────────────────────────────────────────────────────
   Engine Page — The original Manikan avatar engine (standalone)
   ───────────────────────────────────────────────────────────────────────── */
function EnginePage() {
  const [modelUrl, setModelUrl] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const previousUrlRef = useRef(null)

  const handleGenerate = useCallback(async (measurements) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(measurements),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)

      if (previousUrlRef.current) {
        URL.revokeObjectURL(previousUrlRef.current)
      }
      previousUrlRef.current = url
      setModelUrl(url)
    } catch (err) {
      console.error('Avatar generation failed:', err)
      setError(err.message || 'Failed to generate avatar. Is the backend running?')
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-primary">
      <aside className="w-[380px] min-w-[340px] flex-shrink-0">
        <ControlPanel onGenerate={handleGenerate} isLoading={isLoading} />
      </aside>
      <main className="flex-1 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-surface-primary via-surface-secondary to-surface-primary" />
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/[0.03] rounded-full blur-[120px] -translate-y-1/2 translate-x-1/4 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-accent-secondary/[0.03] rounded-full blur-[100px] translate-y-1/2 -translate-x-1/4 pointer-events-none" />
        <div className="relative z-[1] w-full h-full">
          <AvatarViewer modelUrl={modelUrl} isLoading={isLoading} />
        </div>
        {error && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 animate-fade-in">
            <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-danger/10 border border-danger/20 backdrop-blur-md shadow-lg">
              <svg className="w-5 h-5 text-danger flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p className="text-sm text-danger font-medium">{error}</p>
              <button onClick={() => setError(null)} className="ml-2 text-danger/60 hover:text-danger transition-colors cursor-pointer">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────────
   App — Router root
   ───────────────────────────────────────────────────────────────────────── */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<StorePage />} />
      <Route path="/product/:id" element={<ProductDetailPage />} />
      <Route path="/engine" element={<EnginePage />} />
    </Routes>
  )
}
