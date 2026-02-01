#!/usr/bin/env python3
"""Download reference genomes from an input table and compute genome metrics."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

IS_KEYWORDS = [
    "insertion sequence",
    "transposase",
    "mobile element",
    "mobile_element",
    "insertion-sequence",
    "IS element",
]

IS_REGEX = re.compile(r"\bIS\d+\b", re.IGNORECASE)


@dataclass
class AssemblyMeta:
    accession: str
    species: str
    taxonomy_id: Optional[int]
    assembly_level: Optional[str]
    release_date: Optional[str]
    strain: Optional[str]
    species_ani: Optional[str]
    total_sequence_length: Optional[int]
    gc_count: Optional[int]
    atgc_count: Optional[int]
    gc_percent: Optional[float]
    total_cdss: Optional[int]
    pseudogenes: Optional[int]


def run_accession_download(zip_path: Path, accession: str) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "datasets",
        "download",
        "genome",
        "accession",
        accession,
        "--include",
        "genome,gff3",
        "--filename",
        str(zip_path),
    ]

    print("Running:", " ".join(args))
    subprocess.run(args, check=True)


def unzip_dataset(zip_path: Path, dataset_root: Path, force: bool) -> Path:
    if dataset_root.exists() and force:
        shutil.rmtree(dataset_root)
    if dataset_root.exists():
        return dataset_root

    dataset_root.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dataset_root.parent)
    return dataset_root


def load_curation(path: Optional[Path]) -> Dict[str, Dict[str, str]]:
    if not path or not path.exists():
        return {}
    curation: Dict[str, Dict[str, str]] = {}
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            species = (row.get("species") or "").strip()
            accession = (row.get("assembly_accession") or "").strip()
            if accession:
                curation[accession] = {
                    "species": species,
                    "factoid": (row.get("factoid") or "").strip(),
                    "display_species": (row.get("display_species") or "").strip(),
                    "display_strain_name": (row.get("display_strain_name") or "").strip(),
                }
    return curation


def load_metadata(report_path: Path) -> Dict[str, AssemblyMeta]:
    meta: Dict[str, AssemblyMeta] = {}
    if not report_path.exists():
        return meta

    with report_path.open("r") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            accession = record.get("accession") or record.get("assembly_accession") or record.get("currentAccession")
            organism = record.get("organism", {})
            species = (
                organism.get("organismName")
                or organism.get("organism_name")
                or organism.get("taxon", {}).get("name")
            )
            taxonomy_id = organism.get("tax_id") or organism.get("taxId") or organism.get("taxon", {}).get("tax_id")
            assembly_info = record.get("assemblyInfo") or {}
            assembly_stats = record.get("assemblyStats") or {}
            annotation_info = record.get("annotationInfo") or {}
            annotation_stats = annotation_info.get("stats", {})
            gene_counts = annotation_stats.get("geneCounts", {})
            ani_info = record.get("averageNucleotideIdentity") or {}
            ani_best = ani_info.get("bestAniMatch") or {}

            assembly_level = record.get("assembly_level") or assembly_info.get("assemblyLevel")
            release_date = record.get("release_date") or assembly_info.get("releaseDate")
            strain = organism.get("infraspecific_names", {}).get("strain") or organism.get("infraspecificNames", {}).get(
                "strain"
            )
            species_ani = ani_best.get("organismName")

            total_sequence_length = assembly_stats.get("totalSequenceLength")
            gc_count = assembly_stats.get("gcCount")
            atgc_count = assembly_stats.get("atgcCount")
            gc_percent = assembly_stats.get("gcPercent")
            total_cdss = gene_counts.get("proteinCoding") or gene_counts.get("total")
            pseudogenes = gene_counts.get("pseudogene")

            if not accession or not species:
                continue
            meta[accession] = AssemblyMeta(
                accession=accession,
                species=species,
                taxonomy_id=taxonomy_id,
                assembly_level=assembly_level,
                release_date=release_date,
                strain=strain,
                species_ani=species_ani,
                total_sequence_length=int(total_sequence_length) if total_sequence_length else None,
                gc_count=int(gc_count) if gc_count else None,
                atgc_count=int(atgc_count) if atgc_count else None,
                gc_percent=float(gc_percent) if gc_percent is not None else None,
                total_cdss=int(total_cdss) if total_cdss else None,
                pseudogenes=int(pseudogenes) if pseudogenes else None,
            )
    return meta


def parse_fasta(path: Path) -> Tuple[int, int, int]:
    total_len = 0
    gc = 0
    n_count = 0
    with path.open("r") as handle:
        for line in handle:
            if not line or line.startswith(">"):
                continue
            seq = line.strip().upper()
            total_len += len(seq)
            gc += seq.count("G") + seq.count("C")
            n_count += seq.count("N")
    return total_len, gc, n_count


def parse_gff(path: Path) -> Tuple[int, int, int, int]:
    total_cdss = 0
    pseudogenes = 0
    is_elements = 0
    trnas = 0

    with path.open("r") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9:
                continue
            feature_type = parts[2]
            attrs = parse_gff_attributes(parts[8])

            if feature_type == "CDS":
                total_cdss += 1
                if "pseudo" in attrs or attrs.get("pseudogene"):
                    pseudogenes += 1

            if feature_type == "pseudogene":
                pseudogenes += 1

            if feature_type == "tRNA":
                trnas += 1

            if is_is_element(feature_type, attrs):
                is_elements += 1

    return total_cdss, pseudogenes, is_elements, trnas


def parse_gff_attributes(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for item in attr_text.split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            attrs[key] = value
        else:
            attrs[item] = ""
    return attrs


def is_is_element(feature_type: str, attrs: Dict[str, str]) -> bool:
    if feature_type in {"mobile_element", "repeat_region", "insertion_sequence", "transposable_element"}:
        return True

    for key in ("product", "note", "gene", "mobile_element_type"):
        value = attrs.get(key, "")
        if not value:
            continue
        lower = value.lower()
        if any(word in lower for word in IS_KEYWORDS):
            return True
        if IS_REGEX.search(value):
            return True
    return False


def find_assemblies(dataset_root: Path) -> List[Path]:
    data_root = dataset_root / "data"
    if not data_root.exists():
        return []

    assembly_dirs = []
    for path in data_root.iterdir():
        if path.is_dir() and path.name != "dataset_catalog.json":
            assembly_dirs.append(path)
    return assembly_dirs


def pick_file(paths: Iterable[Path], preferred_tokens: List[str]) -> Optional[Path]:
    paths = list(paths)
    for token in preferred_tokens:
        for p in paths:
            if token in p.name:
                return p
    return paths[0] if paths else None


def load_reference_rows(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())

    rows: List[Dict[str, object]] = []
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(dict(row))
    return rows


def extract_accession(row: Dict[str, object]) -> Optional[str]:
    accession = row.get("assembly_accession") or row.get("accession")
    if isinstance(accession, str):
        return accession.strip() or None
    return None


def select_assembly_dir(dataset_root: Path, accession: str) -> Optional[Path]:
    assemblies = find_assemblies(dataset_root)
    for path in assemblies:
        if path.name == accession:
            return path
    return assemblies[0] if assemblies else None


def assemble_metrics(
    assembly_dir: Path, meta_map: Dict[str, AssemblyMeta], curation: Dict[str, Dict[str, str]]
) -> Optional[Dict[str, object]]:
    fasta_files = list(assembly_dir.rglob("*.fna"))
    gff_files = list(assembly_dir.rglob("*.gff")) + list(assembly_dir.rglob("*.gff3"))

    fasta_path = pick_file(fasta_files, ["genomic.fna", "genome.fna"])
    gff_path = pick_file(gff_files, ["genomic.gff", "genome.gff", ".gff3"])

    if not fasta_path or not gff_path:
        return None

    accession = assembly_dir.name
    meta = meta_map.get(accession)
    species = meta.species if meta and meta.species else accession

    total_len, gc, _ = parse_fasta(fasta_path)
    gff_total_cdss, gff_pseudogenes, is_elements, trnas = parse_gff(gff_path)

    meta_total_len = meta.total_sequence_length if meta else None
    meta_gc = meta.gc_count if meta else None
    meta_atgc = meta.atgc_count if meta else None
    meta_gc_pct = meta.gc_percent if meta else None
    meta_total_cdss = meta.total_cdss if meta else None
    meta_pseudogenes = meta.pseudogenes if meta else None

    genome_len = meta_total_len or total_len
    genome_size_mb = genome_len / 1_000_000 if genome_len else 0
    if meta_gc is not None and meta_atgc:
        gc_content_pct = (meta_gc / meta_atgc * 100) if meta_atgc else 0
    else:
        gc_content_pct = (gc / total_len * 100) if total_len else 0

    total_cdss = meta_total_cdss if meta_total_cdss is not None else gff_total_cdss
    pseudogenes = meta_pseudogenes if meta_pseudogenes is not None else gff_pseudogenes
    is_elements_per_mb = (is_elements / genome_size_mb) if genome_size_mb else 0

    curated = curation.get(accession, {})
    factoid = curated.get("factoid", "")
    display_species = curated.get("display_species", "")
    display_strain_name = curated.get("display_strain_name", "")

    return {
        "species": species,
        "assembly_accession": accession,
        "taxonomy_id": meta.taxonomy_id if meta else None,
        "assembly_level": meta.assembly_level if meta else None,
        "release_date": meta.release_date if meta else None,
        "strain": meta.strain if meta else None,
        "species_ani": meta.species_ani if meta else None,
        "display_species": display_species or None,
        "display_strain_name": display_strain_name or None,
        "genome_size_mb": round(genome_size_mb, 3),
        "total_cdss": total_cdss,
        "pseudogenes": pseudogenes,
        "trna": trnas,
        "gc_content_pct": round(gc_content_pct, 2),
        "is_elements": is_elements,
        "is_elements_per_mb": round(is_elements_per_mb, 3),
        "factoid": factoid,
    }


def write_json(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(rows, handle, indent=2)


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_missing_curation(path: Path, rows: List[Dict[str, object]]) -> None:
    existing: Dict[str, Dict[str, str]] = {}
    fieldnames = ["assembly_accession", "species", "factoid", "display_species", "display_strain_name"]
    if path.exists():
        with path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames:
                fieldnames = list(reader.fieldnames)
            for row in reader:
                accession = (row.get("assembly_accession") or "").strip()
                if accession:
                    existing[accession] = row
    else:
        path.parent.mkdir(parents=True, exist_ok=True)

    new_rows = []
    for row in rows:
        accession = row.get("assembly_accession")
        if not accession or accession in existing:
            continue
        new_rows.append(
            {
                "assembly_accession": accession,
                "species": row.get("species") or "",
                "factoid": "",
                "display_species": "",
                "display_strain_name": "",
            }
        )

    if not new_rows:
        return

    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if path.stat().st_size == 0:
            writer.writeheader()
        writer.writerows(new_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute genome metrics for reference genomes in a table.")
    parser.add_argument(
        "--input-table",
        default="data/reference_genomes.json",
        help="Input reference table (CSV or JSON).",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows processed.")
    parser.add_argument("--work-dir", default=".genome_cache", help="Working directory for downloads.")
    parser.add_argument("--out-json", default="public/data/genomes.json", help="Output JSON path.")
    parser.add_argument("--out-csv", default=None, help="Optional output CSV path.")
    parser.add_argument("--curation", default="data/curation.csv", help="Curation CSV path.")
    parser.add_argument("--skip-download", action="store_true", help="Skip NCBI download step.")
    parser.add_argument("--force", action="store_true", help="Force re-extraction of dataset.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    reference_rows = load_reference_rows(Path(args.input_table))
    if not reference_rows:
        print("No rows found in input table.")
        return 1

    if args.limit:
        reference_rows = reference_rows[: args.limit]

    curation_path = Path(args.curation) if args.curation else None
    curation = load_curation(curation_path)

    rows: List[Dict[str, object]] = []
    for ref_row in reference_rows:
        accession = extract_accession(ref_row)
        if not accession:
            continue

        accession_dir = work_dir / "assemblies" / accession
        zip_path = accession_dir / "ncbi_dataset.zip"
        dataset_root = accession_dir / "ncbi_dataset"

        if not args.skip_download:
            if zip_path.exists() and not args.force:
                print(f"Using cached download for {accession}")
            else:
                run_accession_download(zip_path, accession)

        dataset_root = unzip_dataset(zip_path, dataset_root, args.force)
        report_path = dataset_root / "data" / "assembly_data_report.jsonl"
        meta_map = load_metadata(report_path)

        assembly_dir = select_assembly_dir(dataset_root, accession)
        if not assembly_dir:
            continue

        row = assemble_metrics(assembly_dir, meta_map, curation)
        if row:
            if "taxid_input" in ref_row and "taxid_input" not in row:
                row["taxid_input"] = ref_row.get("taxid_input")
            if "phylum" in ref_row:
                row["phylum"] = ref_row.get("phylum")
            if "gram_stain" in ref_row:
                row["gram_stain"] = ref_row.get("gram_stain")
            if "who_priority" in ref_row:
                row["who_priority"] = ref_row.get("who_priority")
            rows.append(row)

    if not rows:
        print("No assemblies found. Check that the dataset includes genome + gff3 files.")
        return 1

    write_json(rows, Path(args.out_json))
    if args.out_csv:
        write_csv(rows, Path(args.out_csv))

    if curation_path:
        append_missing_curation(curation_path, rows)

    print(f"Wrote {len(rows)} assemblies to {args.out_json}")
    if args.out_csv:
        print(f"Wrote CSV to {args.out_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
