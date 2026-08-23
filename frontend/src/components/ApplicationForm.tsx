import {
  useState,
  type FormEvent,
} from 'react'

import { createApplication } from '../api/applications'
import {
  applicationStatuses,
  applicationStatusLabels,
  applicationSources,
  applicationSourceLabels,
  type ApplicationSource,
  type ApplicationStatus,
} from '../types/application'

interface ApplicationFormProps {
  onCreated: () => void
}

type SubmissionState =
  | 'idle'
  | 'submitting'
  | 'success'
  | 'error'

export function ApplicationForm({
  onCreated,
}: ApplicationFormProps) {
  const [companyName, setCompanyName] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [status, setStatus] =
    useState<ApplicationStatus>('draft')
  const [followUpAt, setFollowUpAt] = useState('')
  const [source, setSource] =
    useState<ApplicationSource | ''>('')
  const [jobUrl, setJobUrl] = useState('')
  const [notes, setNotes] = useState('')
  const [submissionState, setSubmissionState] =
    useState<SubmissionState>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    setSubmissionState('submitting')
    setErrorMessage('')

    try {
      await createApplication({
        company_name: companyName.trim(),
        job_title: jobTitle.trim(),
        status,
        follow_up_at:
          followUpAt === ''
            ? null
            : new Date(followUpAt).toISOString(),
        source: source === '' ? null : source,
        job_url: jobUrl.trim() || null,
        notes: notes.trim(),
      })

      setCompanyName('')
      setJobTitle('')
      setStatus('draft')
      setFollowUpAt('')
      setSource('')
      setJobUrl('')
      setNotes('')
      setSubmissionState('success')
      onCreated()
    } catch (error) {
      setSubmissionState('error')
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Başvuru kaydedilemedi.',
      )
    }
  }

  const isSubmitting =
    submissionState === 'submitting'

  return (
    <section
      className="application-form-section"
      aria-labelledby="new-application-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Yeni kayıt</p>
          <h2 id="new-application-title">
            Başvuru ekle
          </h2>
        </div>
      </div>

      <form
        className="application-form"
        onSubmit={(event) => {
          void handleSubmit(event)
        }}
      >
        <label className="form-field">
          <span>Şirket adı</span>
          <input
            type="text"
            value={companyName}
            onChange={(event) => {
              setCompanyName(event.target.value)
            }}
            required
            disabled={isSubmitting}
            placeholder="Örn. OpenAI"
          />
        </label>

        <label className="form-field">
          <span>Pozisyon</span>
          <input
            type="text"
            value={jobTitle}
            onChange={(event) => {
              setJobTitle(event.target.value)
            }}
            required
            disabled={isSubmitting}
            placeholder="Örn. Backend Engineer"
          />
        </label>

        <label className="form-field">
          <span>Başlangıç durumu</span>
          <select
            value={status}
            onChange={(event) => {
              setStatus(
                event.target.value as ApplicationStatus,
              )
            }}
            disabled={isSubmitting}
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
        </label>

        <label className="form-field">
          <span>Takip tarihi</span>
          <input
            type="datetime-local"
            value={followUpAt}
            onChange={(event) => {
              setFollowUpAt(event.target.value)
            }}
            disabled={isSubmitting}
          />
        </label>

        <label className="form-field">
          <span>Başvuru kaynağı</span>
          <select
            value={source}
            onChange={(event) => {
              setSource(
                event.target.value as ApplicationSource | '',
              )
            }}
            disabled={isSubmitting}
          >
            <option value="">Belirtilmedi</option>
            {applicationSources.map(
              (applicationSource) => (
                <option
                  key={applicationSource}
                  value={applicationSource}
                >
                  {
                    applicationSourceLabels[
                      applicationSource
                    ]
                  }
                </option>
              ),
            )}
          </select>
        </label>

        <label className="form-field">
          <span>İlan bağlantısı</span>
          <input
            type="url"
            value={jobUrl}
            onChange={(event) => {
              setJobUrl(event.target.value)
            }}
            disabled={isSubmitting}
            placeholder="https://…"
          />
        </label>

        <label className="form-field form-field--wide">
          <span>Notlar</span>
          <textarea
            value={notes}
            onChange={(event) => {
              setNotes(event.target.value)
            }}
            disabled={isSubmitting}
            maxLength={5000}
            rows={3}
            placeholder="Görüşme notları, iletişim bilgileri veya sonraki adım…"
          />
        </label>

        <div className="form-actions">
          <button
            className="primary-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Kaydediliyor…'
              : 'Başvuruyu kaydet'}
          </button>

          {submissionState === 'success' && (
            <p
              className="form-feedback form-feedback--success"
              role="status"
            >
              Başvuru başarıyla kaydedildi.
            </p>
          )}

          {submissionState === 'error' && (
            <p
              className="form-feedback form-feedback--error"
              role="alert"
            >
              {errorMessage}
            </p>
          )}
        </div>
      </form>
    </section>
  )
}
