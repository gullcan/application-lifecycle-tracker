export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers)

  if (
    options.body !== undefined &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const payload: unknown = await response
      .json()
      .catch(() => null)

    let message =
      `API request failed with status ${response.status}`

    if (
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
    ) {
      message = payload.detail
    }

    throw new Error(message)
  }

  return (await response.json()) as T
}