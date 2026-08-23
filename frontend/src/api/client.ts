export async function apiRequest<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    signal,
  })

  if (!response.ok) {
    throw new Error(
      `API request failed with status ${response.status}`,
    )
  }

  return (await response.json()) as T
}