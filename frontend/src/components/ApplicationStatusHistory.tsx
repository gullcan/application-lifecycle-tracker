import {
  applicationStatusLabels,
  type ApplicationStatusChange,
} from '../types/application'

interface ApplicationStatusHistoryProps {
  history: ApplicationStatusChange[]
}

const dateTimeFormatter = new Intl.DateTimeFormat(
  'tr-TR',
  {
    dateStyle: 'medium',
    timeStyle: 'short',
  },
)

export function ApplicationStatusHistory({
  history,
}: ApplicationStatusHistoryProps) {
  if (history.length === 0) {
    return (
      <span className="history-empty">
        Değişiklik yok
      </span>
    )
  }

  return (
    <details className="status-history">
      <summary>
        {history.length} durum değişikliği
      </summary>

      <ol>
        {history.map((change) => (
          <li
            key={
              `${change.changed_at}-` +
              `${change.previous_status}-` +
              change.new_status
            }
          >
            <span className="status-history__transition">
              {
                applicationStatusLabels[
                  change.previous_status
                ]
              }
              {' → '}
              {
                applicationStatusLabels[
                  change.new_status
                ]
              }
            </span>

            <time dateTime={change.changed_at}>
              {dateTimeFormatter.format(
                new Date(change.changed_at),
              )}
            </time>
          </li>
        ))}
      </ol>
    </details>
  )
}
