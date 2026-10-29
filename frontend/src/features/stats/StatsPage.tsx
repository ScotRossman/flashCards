type StatsPageProps = {
  questionsAnswered: number
  correctAnswers: number
}

function AccuracyStats({
  questionsAnswered,
  correctAnswers,
}: StatsPageProps) {
  const accuracy = questionsAnswered
    ? Math.round((correctAnswers / questionsAnswered) * 100)
    : 0

  return (
    <dl className="stats-list">
      <div>
        <dt>Questions checked</dt>
        <dd>{questionsAnswered}</dd>
      </div>
      <div>
        <dt>Correct answers</dt>
        <dd>{correctAnswers}</dd>
      </div>
      <div>
        <dt>Accuracy</dt>
        <dd>{accuracy}%</dd>
      </div>
    </dl>
  )
}

export function StatsPage({
  questionsAnswered,
  correctAnswers,
}: StatsPageProps) {
  return (
    <div className="stats-page">
      <header className="stats-heading">
        <p className="eyebrow">Your progress</p>
        <h1>My stats</h1>
      </header>

      <div className="stats-sections">
        <section className="practice-card stats-section" aria-labelledby="current-session-title">
          <h2 id="current-session-title">Current session</h2>
          <p className="stats-description">
            Your results since you started this practice session.
          </p>
          <AccuracyStats
            questionsAnswered={questionsAnswered}
            correctAnswers={correctAnswers}
          />
        </section>

        <section className="practice-card stats-section" aria-labelledby="all-sessions-title">
          <h2 id="all-sessions-title">All sessions</h2>
          <p className="stats-description">
            Combined results from recorded practice sessions.
          </p>
          <dl className="stats-list stats-list-unavailable">
            <div>
              <dt>Questions answered</dt>
              <dd>—</dd>
            </div>
            <div>
              <dt>Correct answers</dt>
              <dd>—</dd>
            </div>
            <div>
              <dt>Accuracy</dt>
              <dd>—</dd>
            </div>
          </dl>
          <p className="stats-note" role="status">
            Database-backed stats are not connected to the React app yet.
          </p>
        </section>
      </div>
    </div>
  )
}
