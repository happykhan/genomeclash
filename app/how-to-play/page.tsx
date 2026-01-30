export default function HowToPlayPage() {
  return (
    <section className="about">
      <h1>How to Play</h1>
      <h2 className="howto-heading">Start the game</h2>
      <p>Open Genome Clash and grab a friend. Each player draws a genome card.</p>

      <h2 className="howto-heading">Choose a stat</h2>
      <p>Take turns selecting one genome statistic from your card to compete with.</p>

      <h2 className="howto-heading">Compare values</h2>
      <p>The player with the higher value for the chosen stat wins the round.</p>
      <p>For release dates, the most recent date wins.</p>

      <h2 className="howto-heading">Score points</h2>
      <p>The winner of the round scores one point. Both players then draw a new card.</p>

      <h2 className="howto-heading">Missing values</h2>
      <p>
        If a card shows N/A for a stat, treat it as the lowest possible value for that comparison.
      </p>

      <h2 className="howto-heading">Win the game</h2>
      <p>The first player to reach 10 points wins Genome Clash.</p>
    </section>
  );
}
