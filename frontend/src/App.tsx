import { useEffect, useState } from 'react'

import {
  listApplications,
  listApplicationsNeedingFollowUp,
} from './api/applications'
import { getHealth } from './api/health'
import type { Application } from './types/application'
import {
  applicationStatusLabels,
  terminalApplicationStatuses,
} from './types/application'
import './App.css'

type ApiState = 'checking' | 'online' | 'offline'
type DataState = 'loading' | 'ready' | 'error'

const apiStateLabels: Record<ApiState, string> = {
  checking: 'Kontrol ediliyor',
  online: 'Bağlı',
  offline: 'Bağlantı yok',
}

const dateFormatter = new Intl.DateTimeFormat(
  'tr-TR',
  {
    dateStyle: 'medium',
  },
)

function formatDate(value: string): string {
  return dateFormatter.format(new Date(value))
}

function isAbortError(error: unknown): boolean {
  return (
    error instanceof DOMException &&
    error.name === 'AbortError'
  )
}

function App() {
  const [apiState, setApiState] =
    useState<ApiState>('checking')
  const [dataState, setDataState] =
    useState<DataState>('loading')
  const [applications, setApplications] =
    useState<Application[]>([])
  const [followUpCount, setFollowUpCount] =
    useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function checkApi(): Promise<void> {
      try {
        const health = await getHealth(controller.signal)

        setApiState(
          health.status === 'ok' ? 'online' : 'offline',
        )
      } catch (error) {
        if (!isAbortError(error)) {
          setApiState('offline')
        }
      }
    }

    void checkApi()

    return () => {
      controller.abort()
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    async function loadDashboard(): Promise<void> {
      try {
        const [applicationResults, followUpResults] =
          await Promise.all([
            listApplications(controller.signal),
            listApplicationsNeedingFollowUp(
              new Date(),
              controller.signal,
            ),
          ])

        setApplications(applicationResults)
        setFollowUpCount(followUpResults.length)
        setDataState('ready')
      } catch (error) {
        if (!isAbortError(error)) {
          setDataState('error')
        }
      }
    }

    void loadDashboard()

    return () => {
      controller.abort()
    }
  }, [])

  const activeApplicationCount = applications.filter(
    (application) =>
      !terminalApplicationStatuses.has(
        application.status,
      ),
  ).length

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">
            Application Lifecycle Tracker
          </p>
          <h1>İş başvurularım</h1>
        </div>

        <div
          className={`api-status api-status--${apiState}`}
          role="status"
        >
          <span
            className="api-status__dot"
            aria-hidden="true"
          />
          API: {apiStateLabels[apiState]}
        </div>
      </header>

      <main>
        <section className="intro">
          <div>
            <p className="eyebrow">Kontrol paneli</p>
            <h2>
              Başvuru sürecini tek yerden yönet
            </h2>
            <p className="intro__description">
              Başvurularını, görüşme aşamalarını ve
              takip tarihlerini düzenli olarak izle.
            </p>
          </div>
        </section>

        <section
          className="summary-grid"
          aria-label="Başvuru özeti"
        >
          <article className="summary-card">
            <span>Listelenen başvuru</span>
            <strong>
              {dataState === 'ready'
                ? applications.length
                : '—'}
            </strong>
            <p>İlk 100 başvuru gösteriliyor.</p>
          </article>

          <article className="summary-card">
            <span>Takip bekleyen</span>
            <strong>
              {dataState === 'ready'
                ? followUpCount
                : '—'}
            </strong>
            <p>Bugün ilgilenmen gereken başvurular.</p>
          </article>

          <article className="summary-card">
            <span>Aktif süreçler</span>
            <strong>
              {dataState === 'ready'
                ? activeApplicationCount
                : '—'}
            </strong>
            <p>Henüz terminal duruma ulaşmayan kayıtlar.</p>
          </article>
        </section>

        <section className="applications-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Başvurular</p>
              <h2>Güncel süreçler</h2>
            </div>
          </div>

          {dataState === 'loading' && (
            <p className="state-message">
              Başvurular yükleniyor…
            </p>
          )}

          {dataState === 'error' && (
            <p
              className="state-message state-message--error"
              role="alert"
            >
              Başvurular yüklenemedi. Backend bağlantısını
              kontrol edip sayfayı yenile.
            </p>
          )}

          {dataState === 'ready' &&
            applications.length === 0 && (
              <div className="empty-state">
                <h3>Henüz başvuru bulunmuyor</h3>
                <p>
                  Sonraki adımda yeni başvuru formunu
                  ekleyeceğiz.
                </p>
              </div>
            )}

          {dataState === 'ready' &&
            applications.length > 0 && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Başvuru</th>
                      <th>Durum</th>
                      <th>Takip tarihi</th>
                      <th>Oluşturuldu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.map((application) => (
                      <tr key={application.id}>
                        <td>
                          <strong>
                            {application.company_name}
                          </strong>
                          <span>
                            {application.job_title}
                          </span>
                        </td>
                        <td>
                          <span className="status-badge">
                            {
                              applicationStatusLabels[
                                application.status
                              ]
                            }
                          </span>
                        </td>
                        <td>
                          {application.follow_up_at === null
                            ? 'Planlanmadı'
                            : formatDate(
                                application.follow_up_at,
                              )}
                        </td>
                        <td>
                          {formatDate(
                            application.created_at,
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </section>
      </main>
    </div>
  )
}

export default App