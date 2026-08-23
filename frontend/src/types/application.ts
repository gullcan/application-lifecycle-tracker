export type ApplicationStatus =
  | 'draft'
  | 'applied'
  | 'screening'
  | 'interview'
  | 'offer'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'

export interface ApplicationStatusChange {
  previous_status: ApplicationStatus
  new_status: ApplicationStatus
  changed_at: string
}

export interface Application {
  id: string
  company_name: string
  job_title: string
  status: ApplicationStatus
  created_at: string
  follow_up_at: string | null
  status_history: ApplicationStatusChange[]
}

export const applicationStatusLabels: Record<
  ApplicationStatus,
  string
> = {
  draft: 'Taslak',
  applied: 'Başvuruldu',
  screening: 'Ön görüşme',
  interview: 'Mülakat',
  offer: 'Teklif',
  accepted: 'Kabul edildi',
  rejected: 'Reddedildi',
  withdrawn: 'Geri çekildi',
}

export const terminalApplicationStatuses:
  ReadonlySet<ApplicationStatus> = new Set([
    'accepted',
    'rejected',
    'withdrawn',
  ])