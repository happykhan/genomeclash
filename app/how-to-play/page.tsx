export default function HowToPlayPage() {
  return (
    <section className="about">
      <h1>How to Play</h1>

      <h2 className="howto-heading">Set-up</h2>
      <p>
        Genome Clash is played with 2 players. Each player opens the game in their own web browser,
        or creates a physical deck using the{" "}
        <a href="/print/genome-clash-cards.pdf">print-and-play PDF</a>.
      </p>

      <h2 className="howto-heading">Draw cards</h2>
      <p>
        Each player draws one genome card from their deck.
      </p>

      <h2 className="howto-heading">Choose a stat</h2>
      <p>
        One player chooses a genome statistic from their card and announces it. Both players then
        compare that stat on their cards.
      </p>

      <h2 className="howto-heading">Compare values</h2>
      <p>
        The player with the higher value for the chosen stat wins the round.
      </p>
      <p>
        For release dates, the most oldest date wins.
      </p>

      <h2 className="howto-heading">Score points</h2>
      <p>
        The winner scores one point. Both players discard their cards and draw new ones.
      </p>

      <h2 className="howto-heading">Missing values</h2>
      <p>
        If a card shows <strong>N/A</strong> for a stat, treat it as the lowest possible value for
        that comparison.
      </p>

      <h2 className="howto-heading">Winning the game</h2>
      <p>
        The first player to reach 10 points wins the game.
      </p>
    </section>
  );
}
