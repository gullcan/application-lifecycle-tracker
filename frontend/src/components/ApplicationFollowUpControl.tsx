import {
  useState,
  type FormEvent,
} from 'react'

import {
  clearApplicationFollowUp,
  scheduleApplicationFollowUp,
} from '../api/applications'
import {
  terminalApplicationStatuses,
  type Application,
} from '../types/application'

interface ApplicationFollowUpControlProps {
  application: Application
  onUpdated: () => void
}

type FollowUpAction =
  | 'idle'
  | 'saving'
  | 'clearing'

function toDateTimeLocalValue(
  value: string | null,
): string {
  if (value === null) {
    return ''
  }

  const date = new Date(value)
  const timezoneOffset =
    date.getTimezoneOffset() * 60_000

  return new Date(
    date.getTime() - timezoneOffset,
  )
    .toISOString()
    .slice(0, 16)
}

export function ApplicationFollowUpControl({
  application,
  onUpdated,
}: ApplicationFollowUpControlProps) {
  const [followUpAt, setFollowUpAt] = useState(
    toDateTimeLocalValue(application.follow_up_at),
  )
  const [currentAction, setCurrentAction] =
    useState<FollowUpAction>('idle')
  const [errorMessage, setErrorMessage] =
    useState('')

  const isTerminal =
    terminalApplicationStatuses.has(application.status)
  const isBusy = currentAction !== 'idle'

  async function handleSchedule(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    if (followUpAt === '') {
      return
    }

    setCurrentAction('saving')
    setErrorMessage('')

    try {
      await scheduleApplicationFollowUp(
        application.id,
        new Date(followUpAt).toISOString(),
      )

      onUpdated()
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Takip tarihi kaydedilemedi.',
      )
    } finally {
      setCurrentAction('idle')
    }
  }

  async function handleClear(): Promise<void> {
    setCurrentAction('clearing')
    setErrorMessage('')

    try {
      await clearApplicationFollowUp(
        application.id,
      )

      onUpdated()
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Takip tarihi temizlenemedi.',
      )
    } finally {
      setCurrentAction('idle')
    }
  }

  if (isTerminal) {
    return (
      <div className="follow-up-terminal">
        <span>Takip gerekmiyor</span>
        <small>Süreç kapalı</small>
      </div>
    )
  }

  return (
    <form
      className="follow-up-control"
      onSubmit={(event) => {
        void handleSchedule(event)
      }}
    >
      <input
        type="datetime-local"
        value={followUpAt}
        onChange={(event) => {
          setFollowUpAt(event.target.value)
          setErrorMessage('')
        }}
        required
        disabled={isBusy}
        aria-label={
          `${application.company_name} takip tarihi`
        }
      />

      <div className="follow-up-control__actions">
        <button
          type="submit"
          className="follow-up-save-button"
          disabled={isBusy || followUpAt === ''}
        >
          {currentAction === 'saving'
            ? 'Kaydediliyor…'
            : 'Planla'}
        </button>

        {application.follow_up_at !== null && (
          <button
            type="button"
            className="follow-up-clear-button"
            disabled={isBusy}
            onClick={() => {
              void handleClear()
            }}
          >
            {currentAction === 'clearing'
              ? 'Temizleniyor…'
              : 'Temizle'}
          </button>
        )}
      </div>

      {errorMessage !== '' && (
        <small
          className="follow-up-control__error"
          role="alert"
        >
          {errorMessage}
        </small>
      )}
    </form>
  )
}