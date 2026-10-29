import { useCallback, useEffect, useState } from 'react'
import { getCurrentUser } from 'aws-amplify/auth'
import { Hub } from 'aws-amplify/utils'
import './App.css'
import { PracticePage } from './features/practice/PracticePage'
import { StatsPage } from './features/stats/StatsPage'
import { postAuthenticated } from './services/api'
import {
  authConfigurationError,
  isCognitoConfigured,
  startSignIn,
  startSignOut,
  type SignedInUser,
} from './services/auth'

type Screen = 'practice' | 'stats' | 'databaseMaintenance'
type SessionProgress = Partial<
  Record<number, { correctAnswers: number; questionsAnswered: number }>
>

const practiceTypeNames: Record<number, string> = {
  1: 'addition',
  2: 'subtraction',
  3: 'multiplication',
  4: 'division',
}

function App() {
  const [screen, setScreen] = useState<Screen>('practice')
  const [sessionProgress, setSessionProgress] = useState<SessionProgress>({})
  const [user, setUser] = useState<SignedInUser | null>(null)
  const [authLoading, setAuthLoading] = useState(isCognitoConfigured)
  const [authError, setAuthError] = useState<string | null>(null)

  const refreshUser = useCallback(async () => {
    try {
      setUser(await getCurrentUser())
      setAuthError(null)
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'UserUnAuthenticatedException') {
        setUser(null)
        setAuthError(null)
      } else {
        setAuthError(
          error instanceof Error ? error.message : 'Could not check sign-in status.',
        )
      }
    } finally {
      setAuthLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isCognitoConfigured) {
      return
    }

    const stopListening = Hub.listen('auth', ({ payload }) => {
      if (payload.event === 'signedIn') {
        queueMicrotask(() => {
          void refreshUser()
        })
      } else if (payload.event === 'signedOut') {
        setUser(null)
      } else if (payload.event === 'signInWithRedirect_failure') {
        const eventError =
          typeof payload.data === 'object' &&
          payload.data !== null &&
          'error' in payload.data
            ? payload.data.error
            : null
        setAuthError(
          eventError instanceof Error
            ? eventError.message
            : 'Cognito sign-in did not complete.',
        )
        setAuthLoading(false)
      }
    })

    queueMicrotask(() => {
      void refreshUser()
    })
    return stopListening
  }, [refreshUser])

  async function handleSignIn() {
    setAuthError(null)
    try {
      await startSignIn()
    } catch (error: unknown) {
      setAuthError(
        error instanceof Error ? error.message : 'Could not start Cognito sign-in.',
      )
    }
  }

  async function handleSignOut() {
    setAuthError(null)
    try {
      await startSignOut()
    } catch (error: unknown) {
      setAuthError(
        error instanceof Error ? error.message : 'Could not sign out.',
      )
    }
  }

  function recordAnswer(practiceType: number, isCorrect: boolean) {
    setSessionProgress((progress) => {
      const current = progress[practiceType] ?? {
        correctAnswers: 0,
        questionsAnswered: 0,
      }

      return {
        ...progress,
        [practiceType]: {
          questionsAnswered: current.questionsAnswered + 1,
          correctAnswers: current.correctAnswers + Number(isCorrect),
        },
      }
    })
  }

  async function savePracticeSession(name: string) {
    const sessions = Object.entries(sessionProgress)
      .filter((entry): entry is [string, NonNullable<SessionProgress[number]>] =>
        Boolean(entry[1]?.questionsAnswered),
      )
      .map(([practiceType, progress]) => ({
        practice_type: practiceTypeNames[Number(practiceType)],
        score: progress.correctAnswers,
        total: progress.questionsAnswered,
      }))

    if (sessions.length === 0) {
      setSessionProgress({})
      return false
    }

    if (!user) {
      throw new Error('Sign in before quitting so your session can be saved.')
    }

    await postAuthenticated<{ status: string }>({
      action: 'log_sessions',
      name,
      sessions,
    })
    setSessionProgress({})
    return true
  }

  const questionsAnswered = Object.values(sessionProgress).reduce(
    (total, progress) => total + (progress?.questionsAnswered ?? 0),
    0,
  )
  const correctAnswers = Object.values(sessionProgress).reduce(
    (total, progress) => total + (progress?.correctAnswers ?? 0),
    0,
  )

  return (
    <main className="flashcard-app">
      <header className="auth-bar">
        <div className="auth-status" aria-live="polite">
          {!isCognitoConfigured ? (
            <p className="message error" role="alert">
              {authConfigurationError}
            </p>
          ) : authError ? (
            <p className="message error" role="alert">
              {authError}
            </p>
          ) : authLoading ? (
            <p>Checking sign-in...</p>
          ) : user ? (
            <p>Signed in as {user.username}</p>
          ) : (
            <p>Sign in to use authenticated API features.</p>
          )}
        </div>
        {isCognitoConfigured && !authLoading && (
          <button
            className="auth-button"
            type="button"
            onClick={user ? handleSignOut : handleSignIn}
          >
            {user ? 'Sign out' : 'Sign in'}
          </button>
        )}
      </header>

      <nav className="app-navigation" aria-label="Main navigation">
        <button
          className={screen === 'practice' ? 'active' : ''}
          type="button"
          onClick={() => setScreen('practice')}
          aria-current={screen === 'practice' ? 'page' : undefined}
        >
          Practice
        </button>
        <button
          className={screen === 'stats' ? 'active' : ''}
          type="button"
          onClick={() => setScreen('stats')}
          aria-current={screen === 'stats' ? 'page' : undefined}
        >
          My stats
        </button>
         <button
          className={screen === 'databaseMaintenance' ? 'active' : ''}
          type="button"
          onClick={() => setScreen('databaseMaintenance')}
          aria-current={screen === 'databaseMaintenance' ? 'page' : undefined}
        >
          Database Maintenance
        </button>
      </nav>

      <div hidden={screen !== 'practice'}>
        <PracticePage
          onAnswerChecked={recordAnswer}
          onPracticeReset={savePracticeSession}
        />
      </div>
      <div hidden={screen !== 'stats'}>
        <StatsPage
          questionsAnswered={questionsAnswered}
          correctAnswers={correctAnswers}
        />
      </div>
    </main>
  )
}

export default App
