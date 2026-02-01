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
        genomes from <a href="https://www.ncbi.nlm.nih.gov/refseq/" target="_blank" rel="noopener noreferrer">NCBI RefSeq</a>, computes metrics directly from genome sequences and annotations, and
        compiles the results into a single structured dataset used by the app.
      </p>
      <p>
        Genome Clash is intended for learning, exploration, and scientific curiosity. It is not
        affiliated with NCBI.
      </p>
      <p>
        Made with ❤️ by <a href="https://happykhan.com" target="_blank" rel="noopener noreferrer">Nabil-Fareed Alikhan</a>. Source code available on <a href="https://github.com/happykhan/genomeclash" target="_blank" rel="noopener noreferrer">GitHub</a>.
      </p>
      <div className="about-rules">
        <h2>Quick Rules</h2>
        <ul>
          <li>2 players: open the site separately or use the print-and-play deck.</li>
          <li>Each player draws one card; one player chooses a stat to compare.</li>
          <li>Higher value wins the round (most oldest release date wins).</li>
          <li>Winner scores 1 point; both players draw new cards.</li>
          <li>N/A counts as the lowest value. First to 10 points wins.</li>
        </ul>
      </div>
    </section>
  );
}
