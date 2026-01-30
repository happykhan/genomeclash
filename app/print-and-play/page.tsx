export default function PrintAndPlayPage() {
  return (
    <section className="about">
      <h1>Print and Play</h1>
      <p>
        Download the ready-to-print PDF of Genome Clash cards and print on A4 paper. Each card is
        standard playing-card size (2.5" × 3.5").
      </p>
      <p>
        Steps: generate or update the genome dataset, run the PDF build task, then print the PDF at
        100% scale (no "fit to page"). Cut along the borders to make the cards.
      </p>
      <p>
        <a className="download-link" href="/print/genome-clash-cards.pdf" download>
          Download the print-and-play PDF
        </a>
      </p>
    </section>
  );
}
