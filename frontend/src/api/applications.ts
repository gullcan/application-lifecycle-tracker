import type {
  Application,
  CreateApplicationInput,
} from '../types/application'
import { apiRequest } from './client'

export function listApplications(
  signal?: AbortSignal,
): Promise<Application[]> {
  return apiRequest<Application[]>(
    '/applications?limit=100&offset=0',
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