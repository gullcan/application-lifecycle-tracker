import {
  useState,
  type FormEvent,
} from 'react'

import {
  changeApplicationStatus,
} from '../api/applications'
import {
  applicationStatuses,
  applicationStatusLabels,
  terminalApplicationStatuses,
  type Application,
  type ApplicationStatus,
} from '../types/application'

interface ApplicationStatusControlProps {
  application: Application
  onUpdated: () => void
}

export function ApplicationStatusControl({
  application,
  onUpdated,
}: ApplicationStatusControlProps) {
  const [selectedStatus, setSelectedStatus] =
    useState<ApplicationStatus>(application.status)
  const [isSubmitting, setIsSubmitting] =
    useState(false)
  const [errorMessage, setErrorMessage] =
    useState('')

  const isTerminal =
    terminalApplicationStatuses.has(application.status)

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    if (selectedStatus === application.status) {
      return
    }

    setIsSubmitting(true)
    setErrorMessage('')

    try {
      await changeApplicationStatus(
        application.id,
        selectedStatus,
      )

      onUpdated()
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Durum güncellenemedi.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isTerminal) {
    return (
      <div className="terminal-status">
        <span className="status-badge">
          {applicationStatusLabels[application.status]}
        </span>
        <small>Süreç kapalı</small>
      </div>
    )
  }

  return (
    <form
      className="status-control"
      onSubmit={(event) => {
        void handleSubmit(event)
      }}
    >
      <div className="status-control__inputs">
        <select
          value={selectedStatus}
          onChange={(event) => {
            setSelectedStatus(
              event.target.value as ApplicationStatus,
            )
            setErrorMessage('')
          }}
          disabled={isSubmitting}
          aria-label={
            `${application.company_name} başvuru durumu`
          }
        >
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

        <button
          type="submit"
          className="status-update-button"
          disabled={
            isSubmitting ||
            selectedStatus === application.status
          }
        >
          {isSubmitting ? '…' : 'Güncelle'}
        </button>
      </div>

      {errorMessage !== '' && (
        <small
          className="status-control__error"
          role="alert"
        >
          {errorMessage}
        </small>
      )}
    </form>
  )
}