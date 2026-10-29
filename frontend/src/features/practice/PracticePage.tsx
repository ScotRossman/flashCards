import { useState, type FormEvent } from 'react'
import { getQuestion, type FlashcardQuestion } from '../../services/api'

const practiceTypes = [
  { value: 1, label: 'Addition' },
  { value: 2, label: 'Subtraction' },
  { value: 3, label: 'Multiplication' },
  { value: 4, label: 'Division' },
]

type PracticePageProps = {
  signedInName?: string
  onAnswerChecked: (practiceType: number, isCorrect: boolean) => void
  onPracticeReset: (name: string) => Promise<boolean>
}

export function PracticePage({
  signedInName,
  onAnswerChecked,
  onPracticeReset,
}: PracticePageProps) {
  const [nameOverride, setNameOverride] = useState<string>()
  const name = nameOverride ?? signedInName ?? ''
  const [practiceType, setPracticeType] = useState(1)
  const [question, setQuestion] = useState<FlashcardQuestion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [answerChecked, setAnswerChecked] = useState(false)
  const [answer, setAnswer] = useState('')
  const [answerError, setAnswerError] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  async function loadQuestion() {
    setLoading(true)
    setError(null)
    setAnswerChecked(false)
    setAnswer('')
    setAnswerError(null)
    setIsCorrect(null)

    try {
      setQuestion(await getQuestion(practiceType))
    } catch (requestError: unknown) {
      setQuestion(null)
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not load a flashcard question.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function startPractice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await loadQuestion()
  }

  function checkAnswer() {
    if (!answer.trim() || !question) {
      setAnswerError('Enter your answer before checking.')
      return
    }

    const correct = Number(answer) === question.expected_answer
    setAnswerError(null)
    setIsCorrect(correct)
    setAnswerChecked(true)
    onAnswerChecked(practiceType, correct)
  }

  async function resetApp() {
    setSaving(true)
    setSaveError(null)
    setSaveMessage(null)
    let saved: boolean
    try {
      saved = await onPracticeReset(name.trim())
    } catch (requestError: unknown) {
      setSaveError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not save your practice session.',
      )
      return
    } finally {
      setSaving(false)
    }

    setNameOverride(undefined)
    setPracticeType(1)
    setQuestion(null)
    setError(null)
    setLoading(false)
    setAnswerChecked(false)
    setAnswer('')
    setAnswerError(null)
    setIsCorrect(null)
    setSaveMessage(saved ? 'Practice session saved.' : 'Practice reset.')
  }

  return (
    <div className="practice-layout">
      <section className="practice-card practice-setup" aria-labelledby="practice-title">
        <p className="eyebrow">Math practice</p>
        <h1 id="practice-title">Flashcards</h1>
        <p className="intro">Choose a practice type and get started.</p>

        <form className="practice-form" onSubmit={startPractice}>
          <label htmlFor="player-name">Your name</label>
          <input
            id="player-name"
            name="name"
            type="text"
            autoComplete="given-name"
            maxLength={255}
            placeholder="Enter your name"
            value={nameOverride ?? signedInName ?? ''}
            onChange={(event) => setNameOverride(event.target.value)}
            disabled={saving}
            required
          />

          <label htmlFor="practice-type">What would you like to practice?</label>
          <select
            id="practice-type"
            name="practiceType"
            value={practiceType}
            onChange={(event) => setPracticeType(Number(event.target.value))}
            disabled={saving}
          >
            {practiceTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>

          <button type="submit" disabled={loading || saving}>
            {loading ? 'Loading question...' : 'Start practicing'}
          </button>
          <button type="button" onClick={resetApp} disabled={loading || saving}>
            {saving ? 'Saving session...' : 'Quit practice'}
          </button>
        </form>

        {saveError && (
          <p className="message error" role="alert">
            {saveError}
          </p>
        )}
        {saveMessage && (
          <p className="message" role="status">
            {saveMessage}
          </p>
        )}

        {error && (
          <p className="message error" role="alert">
            {error}
          </p>
        )}
      </section>

      <section className="practice-stage" aria-label="Practice question">
        {question ? (
          <div className="question" aria-live="polite">
            <p className="greeting">You’ve got this, {name.trim()}!</p>
            <h2>{question.question}</h2>
            <label className="answer-label" htmlFor="answer">
              Your answer
            </label>
            <input
              className="answer-input"
              id="answer"
              name="answer"
              type="number"
              inputMode="numeric"
              step="1"
              placeholder="Type your answer"
              value={answer}
              onChange={(event) => {
                setAnswer(event.target.value)
                setAnswerError(null)
              }}
              disabled={answerChecked || loading}
              aria-invalid={answerError !== null}
              aria-describedby={answerError ? 'answer-feedback' : undefined}
            />
            {answerError && (
              <p className="answer-feedback error" id="answer-feedback" role="alert">
                {answerError}
              </p>
            )}
            {answerChecked && (
              <p
                className={`answer-feedback ${isCorrect ? 'correct' : 'incorrect'}`}
                id="answer-feedback"
                role="status"
              >
                {isCorrect
                  ? 'Correct! Great job.'
                  : `Not quite. The correct answer is ${question.expected_answer}.`}
              </p>
            )}
            <div className="answer-actions">
              <button
                id="check-answer"
                className="answer-button primary"
                type="button"
                onClick={checkAnswer}
                disabled={answerChecked || loading}
              >
                Check answer
              </button>
              <button
                className="answer-button secondary"
                type="button"
                onClick={loadQuestion}
                disabled={!answerChecked || loading}
              >
                {loading ? 'Loading...' : 'Next question'}
              </button>
            </div>
          </div>
        ) : (
          <div className="question-placeholder" aria-live="polite">
            {loading ? 'Loading your first question...' : 'Your question will appear here.'}
          </div>
        )}
      </section>
    </div>
  )
}
