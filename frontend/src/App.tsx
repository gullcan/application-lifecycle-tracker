import { useEffect, useState } from 'react'

import {
  listApplications,
  listApplicationsNeedingFollowUp,
} from './api/applications'
import { getHealth } from './api/health'
import { ApplicationForm } from './components/ApplicationForm'
import { ApplicationList } from './components/ApplicationList'
import { DashboardSummary } from './components/DashboardSummary'
import type { Application } from './types/application'
import { terminalApplicationStatuses } from './types/application'
import './App.css'

type ApiState = 'checking' | 'online' | 'offline'
type SummaryState = 'loading' | 'ready' | 'error'

const apiStateLabels: Record<ApiState, string> = {
  checking: 'Kontrol ediliyor',
  online: 'Bağlı',
  offline: 'Bağlantı yok',
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
  const [summaryState, setSummaryState] =
    useState<SummaryState>('loading')
  const [applications, setApplications] =
    useState<Application[]>([])
  const [followUpCount, setFollowUpCount] =
    useState(0)
  const [dashboardVersion, setDashboardVersion] =
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

    async function loadSummary(): Promise<void> {
      try {
        const [applicationResults, followUpResults] =
          await Promise.all([
            listApplications({
              limit: 100,
              offset: 0,
              signal: controller.signal,
            }),
            listApplicationsNeedingFollowUp(
              new Date(),
              controller.signal,
            ),
          ])

        setApplications(applicationResults)
        setFollowUpCount(followUpResults.length)
        setSummaryState('ready')
      } catch (error) {
        if (!isAbortError(error)) {
          setSummaryState('error')
        }
      }
    }

    void loadSummary()

    return () => {
      controller.abort()
    }
  }, [dashboardVersion])

  function refreshDashboard(): void {
    setSummaryState('loading')
    setDashboardVersion(
      (currentVersion) => currentVersion + 1,
    )
  }

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

        <DashboardSummary
          isReady={summaryState === 'ready'}
          totalCount={applications.length}
          followUpCount={followUpCount}
          activeCount={activeApplicationCount}
        />

        {summaryState === 'error' && (
          <p
            className="summary-error"
            role="alert"
          >
            Başvuru özeti yüklenemedi.
          </p>
        )}

        <ApplicationForm
          onCreated={refreshDashboard}
        />

        <ApplicationList
          refreshVersion={dashboardVersion}
          onUpdated={refreshDashboard}
        />
      </main>
    </div>
  )
}

export default App
