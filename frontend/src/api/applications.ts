import type {
  Application,
  ApplicationStatus,
  CreateApplicationInput,
} from '../types/application'
import { apiRequest } from './client'

interface ListApplicationsOptions {
  status?: ApplicationStatus
  limit?: number
  offset?: number
  signal?: AbortSignal
}

export function listApplications({
  status,
  limit = 100,
  offset = 0,
  signal,
}: ListApplicationsOptions = {}): Promise<Application[]> {
  const parameters = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  if (status !== undefined) {
    parameters.set('status', status)
  }

  return apiRequest<Application[]>(
    `/applications?${parameters.toString()}`,
    { signal },
  )
}

export function listApplicationsNeedingFollowUp(
  asOf: Date,
  signal?: AbortSignal,
): Promise<Application[]> {
  const parameters = new URLSearchParams({
    as_of: asOf.toISOString(),
  })

  return apiRequest<Application[]>(
    `/applications/follow-ups?${parameters.toString()}`,
    { signal },
  )
}

export function createApplication(
  input: CreateApplicationInput,
): Promise<Application> {
  return apiRequest<Application>(
    '/applications',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  )
}

export function changeApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
): Promise<Application> {
  return apiRequest<Application>(
    `/applications/${encodeURIComponent(applicationId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    },
  )
}

export function scheduleApplicationFollowUp(
  applicationId: string,
  followUpAt: string,
): Promise<Application> {
  return apiRequest<Application>(
    `/applications/${encodeURIComponent(applicationId)}/follow-up`,
    {
      method: 'PUT',
      body: JSON.stringify({
        follow_up_at: followUpAt,
      }),
    },
  )
}

export function clearApplicationFollowUp(
  applicationId: string,
): Promise<Application> {
  return apiRequest<Application>(
    `/applications/${encodeURIComponent(applicationId)}/follow-up`,
    {
      method: 'DELETE',
    },
  )
}