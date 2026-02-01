"use client";

import { useMemo } from "react";

type MetricGroup = {
  key: string;
  metrics: ReadonlyArray<{ key: string; label: string }>;
};

type GramIndicator = {
  symbol: string;
  label: string;
  key: "positive" | "negative" | "neutral";
};

type GenomeRow = {
  species: string;
  species_ani?: string;
  assembly_accession?: string;
  release_date?: string;
  phylum?: string;
  gram_stain?: string;
  genome_size_mb: number;
  total_cdss: number;
  pseudogenes: number;
  trna?: number;
  gc_content_pct: number;
  is_elements_per_mb: number;
  factoid?: string;
  strain?: string;
  display_strain_name?: string;
  display_species?: string;
  who_priority?: boolean | string;
};

function formatMetric(value: number | string | undefined) {
  if (value === undefined || value === null) return "N/A";
  if (typeof value === "string") return value;
  if (Number.isInteger(value)) return value.toString();
  return value.toFixed(2);
}

function buildGramIndicator(gramStain?: string): GramIndicator {
  const value = (gramStain || "").toLowerCase();
  if (value.includes("positive")) return { symbol: "Gram +", label: "Gram-positive", key: "positive" };
  if (value.includes("negative")) return { symbol: "Gram −", label: "Gram-negative", key: "negative" };
  if (value.includes("no cell wall") || value.includes("acid-fast")) {
    return { symbol: "Atypical", label: gramStain || "Atypical", key: "neutral" };
  }
  return { symbol: "Unknown", label: gramStain || "Unknown", key: "neutral" };
}

function normalizePhylumClass(phylum?: string) {
  const value = (phylum || "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
  return `phylum-${value || "unknown"}`;
}

export default function GenomeCard({
  current,
  metricGroups,
}: {
  current: GenomeRow | undefined;
  metricGroups: ReadonlyArray<MetricGroup>;
}) {
  const cardHeader = useMemo(() => {
    if (!current) return "Loading genomes…";
    return current.display_species || current.species_ani || current.species;
  }, [current]);

  const isLongName = useMemo(() => {
    return cardHeader.length >= 25;
  }, [cardHeader]);

  const phylumLabel = useMemo(() => {
    if (!current?.phylum) return "Unknown phylum";
    return current.phylum;
  }, [current]);

  const gramIndicator = useMemo(() => buildGramIndicator(current?.gram_stain), [current]);

  const phylumClass = useMemo(() => normalizePhylumClass(current?.phylum), [current]);

  const strainLabel = useMemo(() => {
    if (!current) return "";
    return current.display_strain_name || current.strain || "";
  }, [current]);

  const isWhoPriority = useMemo(() => {
    if (!current?.who_priority) return false;
    if (typeof current.who_priority === "boolean") return current.who_priority;
    return current.who_priority.toString().toLowerCase() === "true";
  }, [current]);

  const factoidText = current?.factoid || "Factoid coming soon.";
  const isLongFactoid = factoidText.length > 70;

  return (
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
          <h2 style={isLongName ? { fontSize: "1.45rem" } : undefined}>{cardHeader}</h2>
          <p>
            {current?.assembly_accession ?? "Reference genome"}
            {strainLabel ? ` • ${strainLabel}` : ""}
          </p>
        </div>

        <div className="card-metrics">
          {current ? (
            metricGroups.map((group) => (
              <div className="metric-group" key={group.key}>
                {group.metrics.map((metric) => (
                  <div className="metric" key={metric.key}>
                    <span>{metric.label}</span>
                    <strong>{formatMetric((current as Record<string, unknown>)[metric.key] as number | string)}</strong>
                  </div>
                ))}
              </div>
            ))
          ) : (
            <p className="metric-loading">Loading metrics…</p>
          )}
        </div>

        <div className="card-factoid" style={isLongFactoid ? { fontSize: "0.82rem" } : undefined}>
          <p>{factoidText}</p>
        </div>
      </div>
    </div>
  );
}
