import {
  useState,
  type FormEvent,
} from 'react'

import {
  archiveApplication,
  restoreApplication,
  updateApplication,
} from '../api/applications'
import type {
  Application,
  ApplicationSource,
} from '../types/application'
import {
  applicationSourceLabels,
  applicationSources,
} from '../types/application'

interface ApplicationDetailsControlProps {
  application: Application
  onUpdated: () => void
}

export function ApplicationDetailsControl({
  application,
  onUpdated,
}: ApplicationDetailsControlProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [isSubmitting, setIsSubmitting] =
    useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [companyName, setCompanyName] = useState(
    application.company_name,
  )
  const [jobTitle, setJobTitle] = useState(
    application.job_title,
  )
  const [source, setSource] =
    useState<ApplicationSource | ''>(
      application.source ?? '',
    )
  const [jobUrl, setJobUrl] = useState(
    application.job_url ?? '',
  )
  const [notes, setNotes] = useState(
    application.notes,
  )

  async function handleUpdate(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()
    setIsSubmitting(true)
    setErrorMessage('')

    try {
      await updateApplication(application.id, {
        company_name: companyName.trim(),
        job_title: jobTitle.trim(),
        source: source === '' ? null : source,
        job_url: jobUrl.trim() || null,
        notes: notes.trim(),
      })
      setIsEditing(false)
      onUpdated()
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Başvuru güncellenemedi.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleArchiveChange(): Promise<void> {
    setIsSubmitting(true)
    setErrorMessage('')

    try {
      if (application.archived_at === null) {
        await archiveApplication(application.id)
      } else {
        await restoreApplication(application.id)
      }
      onUpdated()
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Arşiv durumu değiştirilemedi.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <details className="application-details">
      <summary>Detaylar ve düzenleme</summary>

      {!isEditing && (
        <div className="application-details__content">
          <dl>
            <div>
              <dt>Kaynak</dt>
              <dd>
                {application.source === null
                  ? 'Belirtilmedi'
                  : applicationSourceLabels[
                      application.source
                    ]}
              </dd>
            </div>
            <div>
              <dt>İlan</dt>
              <dd>
                {application.job_url === null ? (
                  'Eklenmedi'
                ) : (
                  <a
                    href={application.job_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    İlanı aç
                  </a>
                )}
              </dd>
            </div>
            <div className="application-details__notes">
              <dt>Notlar</dt>
              <dd>
                {application.notes || 'Not eklenmedi'}
              </dd>
            </div>
          </dl>

          <div className="inline-actions">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
            >
              Düzenle
            </button>
            <button
              className="secondary-danger-button"
              type="button"
              disabled={isSubmitting}
              onClick={() => {
                void handleArchiveChange()
              }}
            >
              {application.archived_at === null
                ? 'Arşivle'
                : 'Arşivden çıkar'}
            </button>
          </div>
        </div>
      )}

      {isEditing && (
        <form
          className="details-edit-form"
          onSubmit={(event) => {
            void handleUpdate(event)
          }}
        >
          <label>
            <span>Şirket adı</span>
            <input
              value={companyName}
              onChange={(event) => {
                setCompanyName(event.target.value)
              }}
              required
            />
          </label>
          <label>
            <span>Pozisyon</span>
            <input
              value={jobTitle}
              onChange={(event) => {
                setJobTitle(event.target.value)
              }}
              required
            />
          </label>
          <label>
            <span>Kaynak</span>
            <select
              value={source}
              onChange={(event) => {
                setSource(
                  event.target.value as
                    | ApplicationSource
                    | '',
                )
              }}
            >
              <option value="">Belirtilmedi</option>
              {applicationSources.map((value) => (
                <option key={value} value={value}>
                  {applicationSourceLabels[value]}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>İlan bağlantısı</span>
            <input
              type="url"
              value={jobUrl}
              onChange={(event) => {
                setJobUrl(event.target.value)
              }}
            />
          </label>
          <label className="details-edit-form__notes">
            <span>Notlar</span>
            <textarea
              rows={3}
              maxLength={5000}
              value={notes}
              onChange={(event) => {
                setNotes(event.target.value)
              }}
            />
          </label>
          <div className="inline-actions">
            <button
              className="primary-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? 'Kaydediliyor…'
                : 'Değişiklikleri kaydet'}
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
            >
              Vazgeç
            </button>
          </div>
        </form>
      )}

      {errorMessage !== '' && (
        <p className="inline-error" role="alert">
          {errorMessage}
        </p>
      )}
    </details>
  )
}
