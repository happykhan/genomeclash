"use client";

import { useEffect, useMemo, useState } from "react";

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

function formatMetric(value: number | string) {
  if (typeof value === "string") return value;
  if (Number.isInteger(value)) return value.toString();
  return value.toFixed(2);
}

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

  const cardHeader = useMemo(() => {
    if (!current) return "Loading genomes…";
    return current.species_ani || current.species;
  }, [current]);

  const phylumLabel = useMemo(() => {
    if (!current?.phylum) return "Unknown phylum";
    return current.phylum;
  }, [current]);

  const gramIndicator = useMemo(() => {
    const value = (current?.gram_stain || "").toLowerCase();
    if (value.includes("positive")) return { symbol: "Gram +", label: "Gram-positive", key: "positive" };
    if (value.includes("negative")) return { symbol: "Gram −", label: "Gram-negative", key: "negative" };
    if (value.includes("no cell wall") || value.includes("acid-fast")) {
      return { symbol: "Atypical", label: current?.gram_stain || "Atypical", key: "neutral" };
    }
    return { symbol: "Unknown", label: current?.gram_stain || "Unknown", key: "neutral" };
  }, [current]);

  const isWhoPriority = useMemo(() => {
    if (!current?.who_priority) return false;
    if (typeof current.who_priority === "boolean") return current.who_priority;
    return current.who_priority.toString().toLowerCase() === "true";
  }, [current]);

  const phylumClass = useMemo(() => {
    const value = (current?.phylum || "unknown")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
    return `phylum-${value || "unknown"}`;
  }, [current]);

  const strainLabel = useMemo(() => {
    if (!current) return "";
    return current.display_strain_name || current.strain || "";
  }, [current]);

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
        <div className="card" role="article" aria-label="Genome card">
          <div className={`card-frame gram-${gramIndicator.key}`}>
            {isWhoPriority ? <span className="who-star" aria-label="WHO priority pathogen">★</span> : null}
            <div className="card-title">
              <div className="card-title__meta">
                <span className={`phylum-badge ${phylumClass}`}>{phylumLabel}</span>
                <span className="gram-indicator" aria-label={gramIndicator.label} title={gramIndicator.label}>
                  {gramIndicator.symbol}
                </span>
              </div>
              <h2>{cardHeader}</h2>
              <p>
                {current?.assembly_accession ?? "Reference genome"}
                {strainLabel ? ` • ${strainLabel}` : ""}
              </p>
            </div>

            <div className="card-metrics">
              {current ? (
                metricGroups.map((group, groupIndex) => (
                  <div className="metric-group" key={group.key}>
                    {group.metrics.map((metric) => (
                      <div className="metric" key={metric.key}>
                        <span>{metric.label}</span>
                        <strong>{formatMetric(current[metric.key] ?? 0)}</strong>
                      </div>
                    ))}
                  </div>
                ))
              ) : (
                <p className="metric-loading">Loading metrics…</p>
              )}
            </div>

            <div className="card-factoid">
              <p>{current?.factoid || "Factoid coming soon."}</p>
            </div>
          </div>
        </div>

        <div className="card-controls">
          <button className="next" type="button" onClick={nextCard}>
            Next genome
          </button>
          <p>
            {total ? `${index + 1} / ${total}` : "No genomes loaded yet"}
          </p>
        </div>
      </div>
    </section>
  );
}
