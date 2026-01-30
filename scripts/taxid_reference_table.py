#!/usr/bin/env python3
"""Build a reference-genome table from a list of taxids using NCBI Datasets summary."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def read_taxids(path: Path) -> List[str]:
    taxids: List[str] = []
    for line in path.read_text().splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if "," in raw or "\t" in raw:
            raw = raw.replace("\t", ",")
            first = raw.split(",", 1)[0].strip()
        else:
            first = raw
        if not first.isdigit():
            continue
        taxids.append(first)
    return taxids


def normalize_taxid(value: str) -> str:
    return value.strip()


def run_summary(taxon: str, assembly_source: str, assembly_level: str, limit: Optional[int]) -> List[Dict[str, object]]:
    args = [
        "datasets",
        "summary",
        "genome",
        "taxon",
        taxon,
        "--reference",
        "--assembly-level",
        assembly_level,
        "--assembly-source",
        assembly_source,
        "--as-json-lines",
    ]
    if limit:
        args += ["--limit", str(limit)]

    result = subprocess.run(args, check=True, capture_output=True, text=True)
    records: List[Dict[str, object]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def extract_row(record: Dict[str, object], taxid_input: str) -> Dict[str, object]:
    organism = record.get("organism") or {}
    taxonomy = organism.get("taxon") or {}

    accession = record.get("accession") or record.get("assembly_accession")
    species = organism.get("organism_name") or taxonomy.get("name") or ""
    taxonomy_id = organism.get("tax_id") or taxonomy.get("tax_id")

    return {
        "taxid_input": taxid_input,
        "taxonomy_id": taxonomy_id,
        "species": species,
        "assembly_accession": accession,
        "assembly_level": record.get("assembly_level"),
        "assembly_name": record.get("assembly_name"),
        "assembly_source": record.get("assembly_source"),
        "release_date": record.get("release_date"),
        "refseq_category": record.get("refseq_category"),
        "bioproject": record.get("bioproject_accession"),
        "biosample": record.get("biosample_accession"),
    }


def write_json(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2))


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a reference genome table from taxids.")
    parser.add_argument("--taxids", default="taxids", help="Path to taxids file (default: taxids).")
    parser.add_argument("--assembly-source", default="refseq", help="Assembly source (default: refseq).")
    parser.add_argument("--assembly-level", default="complete", help="Assembly level (default: complete).")
    parser.add_argument("--limit", type=int, default=1, help="Limit per taxid (default: 1).")
    parser.add_argument(
        "--out-json",
        default="data/reference_genomes.json",
        help="Output JSON path (default: data/reference_genomes.json).",
    )
    parser.add_argument(
        "--out-csv",
        default="data/reference_genomes.csv",
        help="Output CSV path (default: data/reference_genomes.csv).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    taxids = read_taxids(Path(args.taxids))
    if not taxids:
        print("No taxids found.")
        return 1

    rows: List[Dict[str, object]] = []
    for raw in taxids:
        taxon = normalize_taxid(raw)
        try:
            records = run_summary(taxon, args.assembly_source, args.assembly_level, args.limit)
        except subprocess.CalledProcessError as exc:
            if not taxon.lower().startswith("taxid:"):
                taxon_prefixed = f"taxid:{taxon}"
                try:
                    records = run_summary(
                        taxon_prefixed, args.assembly_source, args.assembly_level, args.limit
                    )
                    taxon = taxon_prefixed
                except subprocess.CalledProcessError as exc_prefixed:
                    print(f"Failed to fetch summary for {taxon_prefixed}: {exc_prefixed}")
                    continue
            else:
                print(f"Failed to fetch summary for {taxon}: {exc}")
                continue

        if not records:
            print(f"No assemblies returned for {taxon}")
            continue

        rows.append(extract_row(records[0], raw))

    if not rows:
        print("No reference genomes resolved.")
        return 1

    write_json(rows, Path(args.out_json))
    write_csv(rows, Path(args.out_csv))
    print(f"Wrote {len(rows)} rows to {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
