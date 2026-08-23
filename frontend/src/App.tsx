import { useEffect, useState } from 'react'

import {
  listApplications,
  listApplicationsNeedingFollowUp,
} from './api/applications'
import { getHealth } from './api/health'
import {
  ApplicationFollowUpControl,
} from './components/ApplicationFollowUpControl'
import { ApplicationForm } from './components/ApplicationForm'
import {
  ApplicationStatusControl,
} from './components/ApplicationStatusControl'
import type {
  Application,
  ApplicationStatus,
} from './types/application'
import {
  applicationStatuses,
  applicationStatusLabels,
  terminalApplicationStatuses,
} from './types/application'
import './App.css'

type ApiState = 'checking' | 'online' | 'offline'
type DataState = 'loading' | 'ready' | 'error'
type StatusFilter = ApplicationStatus | 'all'

const PAGE_SIZE = 10

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
  const [visibleApplications, setVisibleApplications] =
    useState<Application[]>([])
  const [followUpCount, setFollowUpCount] =
    useState(0)
  const [dashboardVersion, setDashboardVersion] =
    useState(0)
  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>('all')
  const [page, setPage] = useState(0)
  const [hasNextPage, setHasNextPage] =
    useState(false)

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

  function refreshDashboard(): void {
    setDataState('loading')
    setDashboardVersion(
      (currentVersion) => currentVersion + 1,
    )
  }

  useEffect(() => {
    const controller = new AbortController()

    async function loadDashboard(): Promise<void> {
      try {
        const pageRequest =
          statusFilter === 'all'
            ? listApplications({
                limit: PAGE_SIZE + 1,
                offset: page * PAGE_SIZE,
                signal: controller.signal,
              })
            : listApplications({
                status: statusFilter,
                limit: PAGE_SIZE + 1,
                offset: page * PAGE_SIZE,
                signal: controller.signal,
              })

        const [
          summaryResults,
          followUpResults,
          pageResults,
        ] = await Promise.all([
          listApplications({
            limit: 100,
            offset: 0,
            signal: controller.signal,
          }),
          listApplicationsNeedingFollowUp(
            new Date(),
            controller.signal,
          ),
          pageRequest,
        ])

        setApplications(summaryResults)
        setFollowUpCount(followUpResults.length)
        setVisibleApplications(
          pageResults.slice(0, PAGE_SIZE),
        )
        setHasNextPage(
          pageResults.length > PAGE_SIZE,
        )
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
  }, [dashboardVersion, page, statusFilter])

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

        <ApplicationForm
          onCreated={refreshDashboard}
        />

        <section className="applications-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Başvurular</p>
              <h2>Güncel süreçler</h2>
            </div>

            <div className="application-list-controls">
              <label className="status-filter">
                <span>Duruma göre filtrele</span>

                <select
                  value={statusFilter}
                  disabled={dataState === 'loading'}
                  onChange={(event) => {
                    setDataState('loading')
                    setStatusFilter(
                      event.target.value as StatusFilter,
                    )
                    setPage(0)
                  }}
                >
                  <option value="all">
                    Tüm durumlar
                  </option>

                  {applicationStatuses.map(
                    (applicationStatus) => (
                      <option
                        key={applicationStatus}
                        value={applicationStatus}
                      >
                        {
                          applicationStatusLabels[
                            applicationStatus
                          ]
                        }
                      </option>
                    ),
                  )}
                </select>
              </label>

              <div
                className="pagination-controls"
                aria-label="Sayfalama"
              >
                <button
                  type="button"
                  disabled={
                    page === 0 ||
                    dataState === 'loading'
                  }
                  onClick={() => {
                    setDataState('loading')
                    setPage(
                      (currentPage) => currentPage - 1,
                    )
                  }}
                >
                  Önceki
                </button>

                <span>Sayfa {page + 1}</span>

                <button
                  type="button"
                  disabled={
                    !hasNextPage ||
                    dataState === 'loading'
                  }
                  onClick={() => {
                    setDataState('loading')
                    setPage(
                      (currentPage) => currentPage + 1,
                    )
                  }}
                >
                  Sonraki
                </button>
              </div>
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
            visibleApplications.length === 0 && (
              <div className="empty-state">
                <h3>
                  {statusFilter === 'all'
                    ? 'Henüz başvuru bulunmuyor'
                    : 'Bu durumda başvuru bulunmuyor'}
                </h3>
                <p>
                  {statusFilter === 'all'
                    ? 'Yukarıdaki formu kullanarak ilk başvurunu ekleyebilirsin.'
                    : 'Başka bir durum filtresi seçebilirsin.'}
                </p>
              </div>
            )}

          {dataState === 'ready' &&
            visibleApplications.length > 0 && (
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
                    {visibleApplications.map(
                      (application) => (
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
                            <ApplicationStatusControl
                              application={application}
                              onUpdated={refreshDashboard}
                            />
                          </td>
                          <td>
                            <ApplicationFollowUpControl
                              application={application}
                              onUpdated={refreshDashboard}
                            />
                          </td>
                          <td>
                            {formatDate(
                              application.created_at,
                            )}
                          </td>
                        </tr>
                      ),
                    )}
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
