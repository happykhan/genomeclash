"use client";

import { useEffect, useState } from "react";
import GenomeCard from "./components/GenomeCard";

type GenomeRow = {
  species: string;
  species_ani?: string;
  assembly_accession?: string;
  taxonomy_id?: number;
  assembly_level?: string;
  release_date?: string;
  phylum?: string;
  gram_stain?: string;
  who_priority?: boolean | string;
  genome_size_mb: number;
  total_cdss: number;
  pseudogenes: number;
  trna?: number;
  gc_content_pct: number;
  is_elements_per_mb: number;
  factoid?: string;
  strain?: string;
  display_strain_name?: string;
};

const metricGroups = [
  {
    key: "structure",
    metrics: [
      { key: "genome_size_mb", label: "Genome size (Mb)" },
      { key: "total_cdss", label: "Total CDS" },
      { key: "pseudogenes", label: "Pseudogenes" },
      { key: "trna", label: "tRNA" },
    ],
  },
  {
    key: "composition",
    metrics: [
      { key: "gc_content_pct", label: "GC content (%)" },
      { key: "is_elements_per_mb", label: "IS elements / Mb" },
    ],
  },
  {
    key: "metadata",
    metrics: [{ key: "release_date", label: "Release date" }],
  },
] as const;

export default function HomePage() {
  const [rows, setRows] = useState<GenomeRow[]>([]);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    fetch("/data/genomes.json")
      .then((res) => res.json())
      .then((data: GenomeRow[]) => {
        const shuffled = [...data];
        for (let i = shuffled.length - 1; i > 0; i -= 1) {
          const j = Math.floor(Math.random() * (i + 1));
          [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        setRows(shuffled);
        setIndex(0);
      })
      .catch(() => setRows([]));
  }, []);

  const current = rows[index];
  const total = rows.length;

  const nextCard = () => {
    if (!rows.length) return;
    setIndex((prev) => (prev + 1) % rows.length);
  };

  return (
    <section className="card-stage">
      <div className="intro">
        <p className="eyebrow">Stat-comparison cards</p>
        <h1>Pick a genome, compare the stats, learn fast.</h1>
        <p className="lede">
          Each card is generated from NCBI reference genomes and computed genome metrics.
        </p>
      </div>

      <div className="card-wrap">
        <GenomeCard current={current} metricGroups={metricGroups} />

        <div className="card-controls">
          <p>
            {total ? `${index + 1} / ${total}` : "No genomes loaded yet"}
          </p>          
          <button className="next" type="button" onClick={nextCard}>
            Next genome
          </button>
        </div>
      </div>
    </section>
  );
}
