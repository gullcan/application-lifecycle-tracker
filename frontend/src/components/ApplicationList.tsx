import { Fragment, useEffect, useState } from 'react'

import {
  applicationExportUrl,
  listApplications,
} from '../api/applications'
import type {
  Application,
  ApplicationStatus,
  ApplicationSort,
} from '../types/application'
import {
  applicationStatuses,
  applicationStatusLabels,
} from '../types/application'
import { ApplicationFollowUpControl } from './ApplicationFollowUpControl'
import { ApplicationStatusControl } from './ApplicationStatusControl'
import { ApplicationStatusHistory } from './ApplicationStatusHistory'
import { ApplicationDetailsControl } from './ApplicationDetailsControl'

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
  const [search, setSearch] = useState('')
  const [includeArchived, setIncludeArchived] =
    useState(false)
  const [sort, setSort] =
    useState<ApplicationSort>('created_desc')
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
                search,
                includeArchived,
                sort,
                signal: controller.signal,
              })
            : await listApplications({
                status: statusFilter,
                limit: PAGE_SIZE + 1,
                offset: page * PAGE_SIZE,
                search,
                includeArchived,
                sort,
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
  }, [
    includeArchived,
    page,
    refreshVersion,
    search,
    sort,
    statusFilter,
  ])

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
          <label className="search-filter">
            <span>Başvurularda ara</span>
            <input
              type="search"
              value={search}
              placeholder="Şirket, pozisyon veya not"
              onChange={(event) => {
                setDataState('loading')
                setSearch(event.target.value)
                setPage(0)
              }}
            />
          </label>

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

          <label className="sort-filter">
            <span>Sıralama</span>
            <select
              value={sort}
              onChange={(event) => {
                setDataState('loading')
                setSort(
                  event.target.value as ApplicationSort,
                )
                setPage(0)
              }}
            >
              <option value="created_desc">
                En yeni
              </option>
              <option value="created_asc">
                En eski
              </option>
              <option value="company_asc">
                Şirket A–Z
              </option>
            </select>
          </label>

          <label className="archive-filter">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(event) => {
                setDataState('loading')
                setIncludeArchived(event.target.checked)
                setPage(0)
              }}
            />
            <span>Arşivlenenleri göster</span>
          </label>

          <a
            className="export-link"
            href={applicationExportUrl()}
            download
          >
            CSV indir
          </a>

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
                  <Fragment key={application.id}>
                  <tr
                    className={
                      application.archived_at === null
                        ? undefined
                        : 'application-row--archived'
                    }
                  >
                    <td>
                      <strong>
                        {application.company_name}
                      </strong>
                      <span>
                        {application.job_title}
                      </span>
                      {application.archived_at !== null && (
                        <span className="archived-badge">
                          Arşivlendi
                        </span>
                      )}
                    </td>
                    <td>
                      {application.archived_at === null ? (
                        <ApplicationStatusControl
                          application={application}
                          onUpdated={
                            handleApplicationUpdated
                          }
                        />
                      ) : (
                        <span className="status-badge">
                          {
                            applicationStatusLabels[
                              application.status
                            ]
                          }
                        </span>
                      )}
                    </td>
                    <td>
                      {application.archived_at === null ? (
                        <ApplicationFollowUpControl
                          application={application}
                          onUpdated={
                            handleApplicationUpdated
                          }
                        />
                      ) : (
                        'Arşivden çıkararak düzenleyebilirsin.'
                      )}
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
                  <tr className="application-details-row">
                    <td colSpan={5}>
                      <ApplicationDetailsControl
                        application={application}
                        onUpdated={
                          handleApplicationUpdated
                        }
                      />
                    </td>
                  </tr>
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </section>
  )
}
