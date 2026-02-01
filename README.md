# Genome Clash

[![Vercel Deploy](https://vercelbadge.vercel.app/api/happykhan/genomeclash)](https://genomeclash.vercel.app)
![Node](https://img.shields.io/badge/node-%3E%3D20-339933?logo=node.js&logoColor=white)
![Pixi](https://img.shields.io/badge/pixi-enabled-4c1?logo=conda-forge&logoColor=white)

Genome Clash is a browser-based, educational genomics card game. It turns bacterial genomes into stat-comparison trading cards built from automatically computed genome metrics.

## Architecture (short)
- **Taxid summary**: `scripts/taxid_reference_table.py` reads `taxids` and resolves each taxid to a reference genome accession + metadata (summary only).
- **Data pipeline**: `scripts/genome_metrics.py` downloads each referenced assembly, computes metrics from sequence + annotation files, and emits a single JSON/CSV table.
- **Web app**: A small Next.js app reads the JSON dataset and renders one genome card at a time with “Next” interaction plus an About page.
- **Print & play**: `scripts/print_cards_pdf.py` builds a ready-to-print PDF of all cards (A4, standard 2.5\" × 3.5\" size).
- **Curation**: `data/curation.csv` provides optional display overrides and factoids keyed by assembly accession.

## Quick start

### 1) Install NCBI Datasets via pixi

```bash
pixi install
```

### 2) Build the reference table from taxids

```bash
npm run taxid-summary -- --taxids taxids --out-json data/reference_genomes.json
```

This produces the list of reference genome accessions and metadata used in the metrics step.

### 3) Generate genome metrics

```bash
npm run genome-metrics -- \
  --limit 30 \
  --input-table data/reference_genomes.json \
  --out-json public/data/genomes.json \
  --out-csv data/genomes.csv
```

This command downloads each assembly from the reference table, calculates genome-wide metrics, and writes a single table.

### 4) Run the web app

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

### 5) Build the print-and-play PDF

```bash
npm run build-pdf -- --input public/data/genomes.json --output public/print/genome-clash-cards.pdf --include-backs
```

The PDF generator expects these font files to match the web UI typography:
- `fonts/Space_Grotesk/static/SpaceGrotesk-Regular.ttf`
- `fonts/Space_Grotesk/static/SpaceGrotesk-Bold.ttf`
- `fonts/IBM_Plex_Serif/static/IBMPlexSerif-Regular.ttf`
- `fonts/IBM_Plex_Serif/static/IBMPlexSerif-SemiBold.ttf`

## Data outputs

The generated table includes, at minimum:
- `species`
- `species_ani`
- `display_strain_name`
- `genome_size_mb`
- `total_cdss`
- `pseudogenes`
- `trna`
- `gc_content_pct`
- `is_elements_per_mb`
- `factoid`

Plus additional metadata when available (assembly accession, taxonomy id, assembly level, release date, etc.).

## Notes
- The IS element count is estimated from annotations using a transparent heuristic (mobile element features or transposase/insertion-sequence keywords). See `scripts/genome_metrics.py` for details.
- The sample dataset in `public/data/genomes.json` is a placeholder schema example and should be replaced by the generated output.

## Local files
- Taxid summary: `scripts/taxid_reference_table.py`
- Data pipeline: `scripts/genome_metrics.py`

## End-to-end workflow
1) Update `taxids` with your taxon IDs (one per line).
2) Run `npm run taxid-summary -- --taxids taxids`.
3) Run `npm run genome-metrics -- --input-table data/reference_genomes.json`.
4) Run the app (`npm run dev`) or build the PDF (`npm run build-pdf -- --include-backs`).
- Curation: `data/curation.csv`
- Web app: `app`, `public`
