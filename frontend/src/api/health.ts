import { apiRequest } from './client'

export interface HealthResponse {
  status: string
}

export function getHealth(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(
    '/health',
    signal,
  )
}