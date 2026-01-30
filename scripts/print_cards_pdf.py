#!/usr/bin/env python3
"""Generate a print-and-play PDF of all genome cards (A4, standard playing-card size)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

CARD_WIDTH = 2.5 * inch
CARD_HEIGHT = 3.5 * inch
COLS = 3
ROWS = 3

FONT_DIR = Path("fonts")
DISPLAY_REGULAR = FONT_DIR / "Space_Grotesk" / "static" / "SpaceGrotesk-Regular.ttf"
DISPLAY_BOLD = FONT_DIR / "Space_Grotesk" / "static" / "SpaceGrotesk-Bold.ttf"
BODY_REGULAR = FONT_DIR / "Crimson_Pro" / "static" / "CrimsonPro-Regular.ttf"
BODY_SEMIBOLD = FONT_DIR / "Crimson_Pro" / "static" / "CrimsonPro-SemiBold.ttf"

FONT_DISPLAY = "SpaceGrotesk"
FONT_DISPLAY_BOLD = "SpaceGrotesk-Bold"
FONT_BODY = "CrimsonPro"
FONT_BODY_SEMIBOLD = "CrimsonPro-SemiBold"


def hex_color(value: str) -> colors.Color:
    value = value.lstrip("#")
    return colors.HexColor(f"#{value}")


@dataclass
class GenomeRow:
    species: str
    assembly_accession: str | None
    assembly_level: str | None
    genome_size_mb: float
    total_cdss: int
    pseudogenes: int
    gc_content_pct: float
    is_elements_per_mb: float
    factoid: str | None


METRICS = [
    ("Genome size (Mb)", "genome_size_mb"),
    ("Total CDS", "total_cdss"),
    ("Pseudogenes", "pseudogenes"),
    ("GC content (%)", "gc_content_pct"),
    ("IS elements / Mb", "is_elements_per_mb"),
]


def load_rows(path: Path) -> List[GenomeRow]:
    data = json.loads(path.read_text())
    rows: List[GenomeRow] = []
    for row in data:
        rows.append(
            GenomeRow(
                species=row.get("species", "Unknown"),
                assembly_accession=row.get("assembly_accession"),
                assembly_level=row.get("assembly_level"),
                genome_size_mb=float(row.get("genome_size_mb", 0)),
                total_cdss=int(row.get("total_cdss", 0)),
                pseudogenes=int(row.get("pseudogenes", 0)),
                gc_content_pct=float(row.get("gc_content_pct", 0)),
                is_elements_per_mb=float(row.get("is_elements_per_mb", 0)),
                factoid=row.get("factoid"),
            )
        )
    return rows


def wrap_text(text: str, font: str, size: float, max_width: float) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if stringWidth(candidate, font, size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def format_metric(value: float | int) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return f"{int(value)}"


def chunked(rows: Sequence[GenomeRow], size: int) -> List[List[GenomeRow]]:
    return [list(rows[i : i + size]) for i in range(0, len(rows), size)]


def draw_card(c: canvas.Canvas, x: float, y: float, row: GenomeRow) -> None:
    # Palette loosely matches the web UI
    card_bg = hex_color("fff9f0")
    card_border = hex_color("2b2b2b")
    accent = hex_color("ff8f2f")
    ink = hex_color("12202a")
    ink_soft = hex_color("3d4a55")
    factoid_bg = colors.Color(0.07, 0.12, 0.16, alpha=0.06)

    radius = 10
    padding = 10

    c.setFillColor(card_bg)
    c.setStrokeColor(card_border)
    c.setLineWidth(2)
    c.roundRect(x, y, CARD_WIDTH, CARD_HEIGHT, radius, stroke=1, fill=1)

    # Icon box
    icon_size = 32
    icon_x = x + padding
    icon_y = y + CARD_HEIGHT - padding - icon_size
    c.setFillColor(colors.Color(1, 0.56, 0.18, alpha=0.2))
    c.setStrokeColor(card_border)
    c.setLineWidth(1.5)
    c.roundRect(icon_x, icon_y, icon_size, icon_size, 6, stroke=1, fill=1)
    c.setFillColor(ink)
    c.setFont(FONT_DISPLAY_BOLD, 11)
    c.drawCentredString(icon_x + icon_size / 2, icon_y + 10, "DNA")

    # Title
    title_x = x + padding
    title_y = icon_y - 8
    c.setFillColor(ink)
    c.setFont(FONT_DISPLAY_BOLD, 11)
    title_lines = wrap_text(row.species, FONT_DISPLAY_BOLD, 11, CARD_WIDTH - 2 * padding)
    for line in title_lines[:2]:
        c.drawString(title_x, title_y, line)
        title_y -= 13

    subtitle = row.assembly_accession or "Reference genome"
    if row.assembly_level:
        subtitle = f"{subtitle} • {row.assembly_level}"
    c.setFillColor(ink_soft)
    c.setFont(FONT_BODY, 8.5)
    subtitle_lines = wrap_text(subtitle, FONT_BODY, 8.5, CARD_WIDTH - 2 * padding)
    for line in subtitle_lines[:2]:
        c.drawString(title_x, title_y, line)
        title_y -= 10

    # Metrics
    metrics_top = title_y - 6
    for label, key in METRICS:
        value = getattr(row, key)
        c.setFillColor(ink_soft)
        c.setFont(FONT_DISPLAY, 8.2)
        c.drawString(title_x, metrics_top, label)
        c.setFillColor(ink)
        c.setFont(FONT_DISPLAY_BOLD, 8.5)
        c.drawRightString(x + CARD_WIDTH - padding, metrics_top, format_metric(value))
        c.setStrokeColor(colors.Color(0.07, 0.12, 0.16, alpha=0.18))
        c.setLineWidth(0.5)
        c.line(title_x, metrics_top - 4, x + CARD_WIDTH - padding, metrics_top - 4)
        metrics_top -= 14

    # Factoid box
    factoid_height = 50
    factoid_y = y + padding
    c.setFillColor(factoid_bg)
    c.setStrokeColor(colors.Color(0.07, 0.12, 0.16, alpha=0.15))
    c.roundRect(
        x + padding,
        factoid_y,
        CARD_WIDTH - 2 * padding,
        factoid_height,
        6,
        stroke=1,
        fill=1,
    )

    factoid_text = row.factoid or "Factoid coming soon."
    c.setFillColor(ink)
    c.setFont(FONT_BODY, 8.2)
    lines = wrap_text(factoid_text, FONT_BODY, 8.2, CARD_WIDTH - 2 * padding - 6)
    text_y = factoid_y + factoid_height - 12
    for line in lines[:3]:
        c.drawString(x + padding + 4, text_y, line)
        text_y -= 11


def draw_card_back(c: canvas.Canvas, x: float, y: float) -> None:
    card_bg = hex_color("fff9f0")
    card_border = hex_color("2b2b2b")
    accent = hex_color("ff8f2f")
    ink = hex_color("12202a")

    radius = 10
    padding = 10

    c.setFillColor(card_bg)
    c.setStrokeColor(card_border)
    c.setLineWidth(2)
    c.roundRect(x, y, CARD_WIDTH, CARD_HEIGHT, radius, stroke=1, fill=1)

    # Center emblem
    emblem_size = 120
    emblem_x = x + (CARD_WIDTH - emblem_size) / 2
    emblem_y = y + (CARD_HEIGHT - emblem_size) / 2
    c.setFillColor(colors.Color(1, 0.56, 0.18, alpha=0.25))
    c.setStrokeColor(card_border)
    c.setLineWidth(1.5)
    c.roundRect(emblem_x, emblem_y, emblem_size, emblem_size, 16, stroke=1, fill=1)

    c.setFillColor(ink)
    c.setFont(FONT_DISPLAY_BOLD, 20)
    c.drawCentredString(x + CARD_WIDTH / 2, emblem_y + emblem_size / 2 + 8, "GC")
    c.setFont(FONT_DISPLAY, 9.5)
    c.drawCentredString(x + CARD_WIDTH / 2, emblem_y + emblem_size / 2 - 10, "Genome Clash")

    # Decorative border ticks
    c.setStrokeColor(accent)
    c.setLineWidth(1.2)
    for i in range(6):
        offset = padding + i * 6
        c.line(x + offset, y + padding, x + offset + 3, y + padding)
        c.line(x + CARD_WIDTH - offset, y + CARD_HEIGHT - padding, x + CARD_WIDTH - offset - 3, y + CARD_HEIGHT - padding)


def compute_grid(page_width: float, page_height: float) -> tuple[float, float, float, float]:
    margin_x = 0.2 * inch
    margin_y = 0.3 * inch
    gap_x = (page_width - 2 * margin_x - COLS * CARD_WIDTH) / (COLS - 1)
    gap_y = (page_height - 2 * margin_y - ROWS * CARD_HEIGHT) / (ROWS - 1)

    if gap_x < 0 or gap_y < 0:
        raise ValueError("Card layout does not fit on the page with current margins.")

    return margin_x, margin_y, gap_x, gap_y


def build_pdf(rows: List[GenomeRow], output: Path, include_backs: bool) -> None:
    page_width, page_height = A4
    margin_x, margin_y, gap_x, gap_y = compute_grid(page_width, page_height)

    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=A4)

    per_page = COLS * ROWS
    for page_rows in chunked(rows, per_page):
        for idx, row in enumerate(page_rows):
            col = idx % COLS
            row_idx = idx // COLS
            x = margin_x + col * (CARD_WIDTH + gap_x)
            y = page_height - margin_y - CARD_HEIGHT - row_idx * (CARD_HEIGHT + gap_y)
            draw_card(c, x, y, row)
        c.showPage()

        if include_backs:
            for idx in range(len(page_rows)):
                # Mirror columns for duplex alignment.
                col = (COLS - 1) - (idx % COLS)
                row_idx = idx // COLS
                x = margin_x + col * (CARD_WIDTH + gap_x)
                y = page_height - margin_y - CARD_HEIGHT - row_idx * (CARD_HEIGHT + gap_y)
                draw_card_back(c, x, y)
            c.showPage()

    c.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a print-ready PDF of Genome Clash cards.")
    parser.add_argument(
        "--input",
        default="public/data/genomes.json",
        help="Input JSON file (default: public/data/genomes.json)",
    )
    parser.add_argument(
        "--output",
        default="public/print/genome-clash-cards.pdf",
        help="Output PDF path (default: public/print/genome-clash-cards.pdf)",
    )
    parser.add_argument(
        "--include-backs",
        action="store_true",
        help="Add a mirrored back page after each front page for duplex printing.",
    )
    return parser.parse_args()


def register_fonts() -> None:
    missing = [p for p in (DISPLAY_REGULAR, DISPLAY_BOLD, BODY_REGULAR, BODY_SEMIBOLD) if not p.exists()]
    if missing:
        missing_list = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(
            "Missing font files required for PDF rendering: "
            f"{missing_list}. Place the font files under the 'fonts/' directory."
        )

    pdfmetrics.registerFont(TTFont(FONT_DISPLAY, str(DISPLAY_REGULAR)))
    pdfmetrics.registerFont(TTFont(FONT_DISPLAY_BOLD, str(DISPLAY_BOLD)))
    pdfmetrics.registerFont(TTFont(FONT_BODY, str(BODY_REGULAR)))
    pdfmetrics.registerFont(TTFont(FONT_BODY_SEMIBOLD, str(BODY_SEMIBOLD)))


def main() -> int:
    args = parse_args()
    rows = load_rows(Path(args.input))
    if not rows:
        print("No genomes found in input JSON.")
        return 1
    build_pdf(rows, Path(args.output), args.include_backs)
    print(f"Wrote PDF to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
