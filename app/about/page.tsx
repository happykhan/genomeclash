export default function AboutPage() {
  return (
    <section className="about">
      <h1>About Genome Clash</h1>
      <p>
        Genome Clash is an educational genomics card game that transforms bacterial reference
        genomes into interactive stat-comparison trading cards. Each card presents genome-derived
        metrics—such as genome size, GC content, coding sequence counts, and mobile element density—
        designed to make comparative genomics intuitive and engaging.
      </p>
      <p>
        All data are generated through an automated pipeline that retrieves bacterial reference
        genomes from NCBI, computes metrics directly from genome sequences and annotations, and
        compiles the results into a single structured dataset used by the app.
      </p>
      <p>
        Genome Clash is intended for learning, exploration, and scientific curiosity. It is not
        affiliated with NCBI.
      </p>
      <p>
        Made with ❤️ by Nabil-Fareed Alikhan. Source code available on <a href="https://github.com/happykhan/genomeclash" target="_blank" rel="noopener noreferrer">GitHub</a>.
      </p>
      <div className="about-rules">
        <h2>Quick Rules</h2>
        <ul>
          <li>Each player draws a genome card.</li>
          <li>Take turns choosing a stat to compare.</li>
          <li>
            The higher value wins the round (for release dates, the most recent wins).
          </li>
          <li>The winner scores 1 point.</li>
          <li>N/A counts as the lowest possible value.</li>
          <li>First to 10 points wins.</li>
        </ul>
      </div>
    </section>
  );
}
