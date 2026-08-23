import type { Application } from '../types/application'

export function makeApplication(
  overrides: Partial<Application> = {},
): Application {
  return {
    id: '123e4567-e89b-12d3-a456-426614174000',
    company_name: 'OpenAI',
    job_title: 'Backend Engineer',
    status: 'applied',
    created_at: '2026-08-24T08:00:00Z',
    follow_up_at: null,
    source: null,
    job_url: null,
    notes: '',
    archived_at: null,
    status_history: [],
    ...overrides,
  }
}
