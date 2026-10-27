import { useState } from 'react'
import './App.css'
import { PracticePage } from './features/practice/PracticePage'
import { StatsPage } from './features/stats/StatsPage'

type Screen = 'practice' | 'stats' | 'databaseMaintenance'

function App() {
  const [screen, setScreen] = useState<Screen>('practice')
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [correctAnswers, setCorrectAnswers] = useState(0)

  function recordAnswer(isCorrect: boolean) {
    setQuestionsAnswered((count) => count + 1)
    if (isCorrect) {
      setCorrectAnswers((count) => count + 1)
    }
  }

  function resetStats() {
    setQuestionsAnswered(0)
    setCorrectAnswers(0)
  }

  return (
    <main className="flashcard-app">
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
          onPracticeReset={resetStats}
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
