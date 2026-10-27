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
