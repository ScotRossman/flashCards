import { getIdentityName, getIdentityToken } from './auth'

export type FlashcardQuestion = {
  status: string
  question: string
  expected_answer: number
}

const apiUrl = import.meta.env.VITE_FLASHCARD_API_URL

export async function getQuestion(
  practiceType: number,
): Promise<FlashcardQuestion> {
  if (!apiUrl) {
    throw new Error('VITE_FLASHCARD_API_URL is not configured.')
  }

  const url = new URL(apiUrl)
  url.searchParams.set('practice_type', String(practiceType))

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Question request failed (${response.status}).`)
  }

  return response.json() as Promise<FlashcardQuestion>
}

export async function postAuthenticated<TResponse>(
  payload: Record<string, unknown>,
): Promise<TResponse> {
  if (!apiUrl) {
    throw new Error('VITE_FLASHCARD_API_URL is not configured.')
  }

  const [identityToken, identityName] = await Promise.all([
    getIdentityToken(),
    getIdentityName(),
  ])
  const requestPayload =
    identityName && 'name' in payload ? { ...payload, name: identityName } : payload
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${identityToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestPayload),
  })

  if (!response.ok) {
    const body: unknown = await response.json()
    const message =
      typeof body === 'object' &&
      body !== null &&
      'error' in body &&
      typeof body.error === 'string'
        ? body.error
        : `Authorized API request failed (${response.status}).`
    throw new Error(message)
  }

  return response.json() as Promise<TResponse>
}
