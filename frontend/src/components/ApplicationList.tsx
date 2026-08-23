import { useEffect, useState } from 'react'

import { listApplications } from '../api/applications'
import type {
  Application,
  ApplicationStatus,
} from '../types/application'
import {
  applicationStatuses,
  applicationStatusLabels,
} from '../types/application'
import { ApplicationFollowUpControl } from './ApplicationFollowUpControl'
import { ApplicationStatusControl } from './ApplicationStatusControl'
import { ApplicationStatusHistory } from './ApplicationStatusHistory'

interface ApplicationListProps {
  refreshVersion: number
  onUpdated: () => void
}

type DataState = 'loading' | 'ready' | 'error'
type StatusFilter = ApplicationStatus | 'all'

const PAGE_SIZE = 10

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

export function ApplicationList({
  refreshVersion,
  onUpdated,
}: ApplicationListProps) {
  const [dataState, setDataState] =
    useState<DataState>('loading')
  const [applications, setApplications] =
    useState<Application[]>([])
  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>('all')
  const [page, setPage] = useState(0)
  const [hasNextPage, setHasNextPage] =
    useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function loadApplications(): Promise<void> {
      try {
        const results =
          statusFilter === 'all'
            ? await listApplications({
                limit: PAGE_SIZE + 1,
                offset: page * PAGE_SIZE,
                signal: controller.signal,
              })
            : await listApplications({
                status: statusFilter,
                limit: PAGE_SIZE + 1,
                offset: page * PAGE_SIZE,
                signal: controller.signal,
              })

        setApplications(
          results.slice(0, PAGE_SIZE),
        )
        setHasNextPage(results.length > PAGE_SIZE)
        setDataState('ready')
      } catch (error) {
        if (!isAbortError(error)) {
          setDataState('error')
        }
      }
    }

    void loadApplications()

    return () => {
      controller.abort()
    }
  }, [page, refreshVersion, statusFilter])

  function handleApplicationUpdated(): void {
    setDataState('loading')
    onUpdated()
  }

  return (
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
        applications.length === 0 && (
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
        applications.length > 0 && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Başvuru</th>
                  <th>Durum</th>
                  <th>Takip tarihi</th>
                  <th>Oluşturuldu</th>
                  <th>Geçmiş</th>
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
                      <ApplicationStatusControl
                        application={application}
                        onUpdated={
                          handleApplicationUpdated
                        }
                      />
                    </td>
                    <td>
                      <ApplicationFollowUpControl
                        application={application}
                        onUpdated={
                          handleApplicationUpdated
                        }
                      />
                    </td>
                    <td>
                      {formatDate(
                        application.created_at,
                      )}
                    </td>
                    <td>
                      <ApplicationStatusHistory
                        history={
                          application.status_history
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </section>
  )
}
