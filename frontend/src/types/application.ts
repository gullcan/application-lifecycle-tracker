export const applicationStatuses = [
  'draft',
  'applied',
  'screening',
  'interview',
  'offer',
  'accepted',
  'rejected',
  'withdrawn',
] as const

export type ApplicationStatus =
  (typeof applicationStatuses)[number]

export const applicationSources = [
  'linkedin',
  'company_website',
  'referral',
  'email',
  'other',
] as const

export type ApplicationSource =
  (typeof applicationSources)[number]

export type ApplicationSort =
  | 'created_desc'
  | 'created_asc'
  | 'company_asc'

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
  source: ApplicationSource | null
  job_url: string | null
  notes: string
  archived_at: string | null
  status_history: ApplicationStatusChange[]
}

export interface CreateApplicationInput {
  company_name: string
  job_title: string
  status: ApplicationStatus
  follow_up_at: string | null
  source: ApplicationSource | null
  job_url: string | null
  notes: string
}

export interface UpdateApplicationInput {
  company_name: string
  job_title: string
  source: ApplicationSource | null
  job_url: string | null
  notes: string
}

export const applicationSourceLabels: Record<
  ApplicationSource,
  string
> = {
  linkedin: 'LinkedIn',
  company_website: 'Şirket sitesi',
  referral: 'Referans',
  email: 'E-posta',
  other: 'Diğer',
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
