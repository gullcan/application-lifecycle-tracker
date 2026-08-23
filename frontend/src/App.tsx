import { useEffect, useState } from 'react'

import { getHealth } from './api/health'
import './App.css'

type ApiState = 'checking' | 'online' | 'offline'

const apiStateLabels: Record<ApiState, string> = {
  checking: 'Kontrol ediliyor',
  online: 'Bağlı',
  offline: 'Bağlantı yok',
}

function App() {
  const [apiState, setApiState] =
    useState<ApiState>('checking')

  useEffect(() => {
    const controller = new AbortController()

    async function checkApi(): Promise<void> {
      try {
        const health = await getHealth(controller.signal)

        setApiState(
          health.status === 'ok' ? 'online' : 'offline',
        )
      } catch (error) {
        if (
          error instanceof DOMException &&
          error.name === 'AbortError'
        ) {
          return
        }

        setApiState('offline')
      }
    }

    void checkApi()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Application Lifecycle Tracker</p>
          <h1>İş başvurularım</h1>
        </div>

        <div
          className={`api-status api-status--${apiState}`}
          role="status"
        >
          <span className="api-status__dot" aria-hidden="true" />
          API: {apiStateLabels[apiState]}
        </div>
      </header>

      <main>
        <section className="intro">
          <div>
            <p className="eyebrow">Kontrol paneli</p>
            <h2>Başvuru sürecini tek yerden yönet</h2>
            <p className="intro__description">
              Başvurularını, görüşme aşamalarını ve takip
              tarihlerini düzenli olarak izle.
            </p>
          </div>
        </section>

        <section
          className="summary-grid"
          aria-label="Başvuru özeti"
        >
          <article className="summary-card">
            <span>Toplam başvuru</span>
            <strong>—</strong>
            <p>Sonraki adımda API’den yüklenecek.</p>
          </article>

          <article className="summary-card">
            <span>Takip bekleyen</span>
            <strong>—</strong>
            <p>Bugün ilgilenmen gereken başvurular.</p>
          </article>

          <article className="summary-card">
            <span>Aktif süreçler</span>
            <strong>—</strong>
            <p>Henüz terminal duruma ulaşmayan kayıtlar.</p>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App