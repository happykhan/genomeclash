#!/usr/bin/env python3
"""Generate a print-and-play PDF of all genome cards (A4, standard playing-card size)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
import math
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
BODY_REGULAR = FONT_DIR / "IBM_Plex_Serif" / "IBMPlexSerif-Regular.ttf"
BODY_SEMIBOLD = FONT_DIR / "IBM_Plex_Serif" / "IBMPlexSerif-SemiBold.ttf"
BODY_ITALIC = FONT_DIR / "IBM_Plex_Serif" / "IBMPlexSerif-Italic.ttf"

FONT_DISPLAY = "SpaceGrotesk"
FONT_DISPLAY_BOLD = "SpaceGrotesk-Bold"
FONT_BODY = "IBMPlexSerif"
FONT_BODY_SEMIBOLD = "IBMPlexSerif-SemiBold"
FONT_BODY_ITALIC = "IBMPlexSerif-Italic"
FONT_MONO = "Courier"


def hex_color(value: str) -> colors.Color:
    value = value.lstrip("#")
    return colors.HexColor(f"#{value}")


@dataclass
class GenomeRow:
    species: str
    species_ani: str | None
    assembly_accession: str | None
    strain: str | None
    display_strain_name: str | None
    phylum: str | None
    gram_stain: str | None
    who_priority: bool
    genome_size_mb: float
    total_cdss: int
    pseudogenes: int
    trna: int
    gc_content_pct: float
    is_elements_per_mb: float
    release_date: str | None
    factoid: str | None


METRICS = [
    ("Genome size (Mb)", "genome_size_mb"),
    ("Total CDS", "total_cdss"),
    ("Pseudogenes", "pseudogenes"),
    ("tRNA", "trna"),
    ("GC content (%)", "gc_content_pct"),
    ("IS elements / Mb", "is_elements_per_mb"),
    ("Release date", "release_date"),
]


def load_rows(path: Path) -> List[GenomeRow]:
    data = json.loads(path.read_text())
    rows: List[GenomeRow] = []
    for row in data:
        rows.append(
            GenomeRow(
                species=row.get("species", "Unknown"),
                species_ani=row.get("species_ani"),
                assembly_accession=row.get("assembly_accession"),
                strain=row.get("strain"),
                display_strain_name=row.get("display_strain_name"),
                phylum=row.get("phylum"),
                gram_stain=row.get("gram_stain"),
                who_priority=parse_bool(row.get("who_priority")),
                genome_size_mb=float(row.get("genome_size_mb", 0)),
                total_cdss=int(row.get("total_cdss", 0)),
                pseudogenes=int(row.get("pseudogenes", 0)),
                trna=int(row.get("trna", 0)),
                gc_content_pct=float(row.get("gc_content_pct", 0)),
                is_elements_per_mb=float(row.get("is_elements_per_mb", 0)),
                release_date=row.get("release_date"),
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


def draw_italic_line(c: canvas.Canvas, x: float, y: float, text: str, font: str, size: float) -> None:
    c.saveState()
    c.setFont(font, size)
    c.translate(x, y)
    c.transform(1, 0, 0.18, 1, 0, 0)
    c.drawString(0, 0, text)
    c.restoreState()


def draw_star(c: canvas.Canvas, cx: float, cy: float, outer: float, inner: float) -> None:
    points = []
    for i in range(10):
        angle = (i * 36) - 90
        radius = outer if i % 2 == 0 else inner
        rad = angle * 3.1415926535 / 180
        x = cx + radius * (math.cos(rad))
        y = cy + radius * (math.sin(rad))
        points.append((x, y))
    path = c.beginPath()
    path.moveTo(points[0][0], points[0][1])
    for x, y in points[1:]:
        path.lineTo(x, y)
    path.close()
    c.drawPath(path, stroke=0, fill=1)


def format_metric(value: float | int | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return f"{int(value)}"


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def gram_key_from_value(value: str | None) -> str:
    gram = (value or "").lower()
    if "positive" in gram:
        return "positive"
    if "negative" in gram:
        return "negative"
    if "no cell wall" in gram or "acid-fast" in gram:
        return "neutral"
    return "neutral"


def gram_border_color(key: str, fallback: colors.Color) -> colors.Color:
    if key == "positive":
        return colors.Color(0.47, 0.34, 0.79, alpha=0.9)
    if key == "negative":
        return colors.Color(0.86, 0.4, 0.52, alpha=0.9)
    return colors.Color(0.43, 0.46, 0.49, alpha=0.8)


def gram_label_from_key(key: str, raw: str | None) -> tuple[str, str]:
    if key == "positive":
        return "GRAM +", "Gram-positive"
    if key == "negative":
        return "GRAM −", "Gram-negative"
    return (raw or "Atypical").upper(), raw or "Atypical"


def gram_pill_colors(key: str) -> tuple[colors.Color, colors.Color]:
    if key == "positive":
        return colors.Color(0.47, 0.34, 0.79, alpha=0.18), hex_color("2f1f61")
    if key == "negative":
        return colors.Color(0.86, 0.4, 0.52, alpha=0.18), hex_color("6b2338")
    return colors.Color(0.43, 0.46, 0.49, alpha=0.18), hex_color("2f3438")


def phylum_colors(phylum: str) -> tuple[colors.Color, colors.Color]:
    key = phylum.strip().lower()
    palette = {
        "firmicutes": (colors.Color(0.13, 0.42, 0.36, alpha=0.16), hex_color("1f4f44")),
        "proteobacteria": (colors.Color(0.75, 0.43, 0.13, alpha=0.16), hex_color("6d3e11")),
        "actinobacteria": (colors.Color(0.81, 0.29, 0.28, alpha=0.16), hex_color("6a1f1e")),
        "bacteroidetes": (colors.Color(0.15, 0.51, 0.67, alpha=0.16), hex_color("0c4f68")),
        "campylobacterota": (colors.Color(0.21, 0.56, 0.42, alpha=0.16), hex_color("1f5a43")),
        "chlamydiota": (colors.Color(0.69, 0.54, 0.19, alpha=0.16), hex_color("6a4e12")),
        "mycoplasmatota": (colors.Color(0.47, 0.5, 0.53, alpha=0.16), hex_color("3f454b")),
    }
    return palette.get(key, (colors.Color(0.07, 0.12, 0.16, alpha=0.08), hex_color("3d4a55")))


def chunked(rows: Sequence[GenomeRow], size: int) -> List[List[GenomeRow]]:
    return [list(rows[i : i + size]) for i in range(0, len(rows), size)]


def draw_card(c: canvas.Canvas, x: float, y: float, row: GenomeRow) -> None:
    # Palette loosely matches the web UI
    card_bg = hex_color("fff9f0")
    card_border = hex_color("1f2326")
    accent = hex_color("ff8f2f")
    ink = hex_color("12202a")
    ink_soft = hex_color("3d4a55")
    factoid_bg = colors.Color(0.07, 0.12, 0.16, alpha=0.06)

    radius = 14
    padding = 12
    top_offset = 8

    gram_key = gram_key_from_value(row.gram_stain)
    gram_border = gram_border_color(gram_key, card_border)
    c.setFillColor(card_bg)
    c.setStrokeColor(gram_border)
    c.setLineWidth(2.2)
    c.roundRect(x, y, CARD_WIDTH, CARD_HEIGHT, radius, stroke=1, fill=1)

    if row.who_priority:
        c.setFillColor(accent)
        draw_star(c, x + CARD_WIDTH - padding - 8, y + CARD_HEIGHT - padding - 6, 6, 2.8)

    # Title
    title_x = x + padding
    title_y = y + CARD_HEIGHT - padding - 10 - top_offset
    display_species = row.species_ani or row.species
    phylum = row.phylum or "Unknown phylum"
    phylum_bg, phylum_text = phylum_colors(phylum)

    # Phylum badge
    badge_height = 14
    badge_padding = 6
    badge_y = title_y + 8
    c.setFont(FONT_DISPLAY, 7.2)
    badge_text_width = stringWidth(phylum.upper(), FONT_DISPLAY, 7.2)
    badge_width = badge_text_width + badge_padding * 2
    c.setFillColor(phylum_bg)
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0))
    c.roundRect(title_x, badge_y, badge_width, badge_height, 8, stroke=0, fill=1)
    c.setFillColor(phylum_text)
    c.drawString(title_x + badge_padding, badge_y + 4, phylum.upper())

    # Gram indicator pill
    gram_text, gram_label = gram_label_from_key(gram_key, row.gram_stain)
    gram_bg, gram_text_color = gram_pill_colors(gram_key)
    gram_width = stringWidth(gram_text, FONT_DISPLAY, 7.2) + badge_padding * 2
    gram_x = title_x + badge_width + 6
    c.setFillColor(gram_bg)
    c.roundRect(gram_x, badge_y, gram_width, badge_height, 8, stroke=0, fill=1)
    c.setFillColor(gram_text_color)
    c.drawString(gram_x + badge_padding, badge_y + 4, gram_text)

    title_y -= 8
    c.setFillColor(ink)
    c.setFont(FONT_DISPLAY_BOLD, 11)
    title_lines = wrap_text(display_species, FONT_DISPLAY_BOLD, 11, CARD_WIDTH - 2 * padding)
    for line in title_lines[:2]:
        draw_italic_line(c, title_x, title_y, line, FONT_DISPLAY_BOLD, 11)
        title_y -= 13

    subtitle = row.assembly_accession or "Reference genome"
    strain = row.display_strain_name or row.strain
    if strain:
        subtitle = f"{subtitle} • {strain}"
    c.setFillColor(ink_soft)
    c.setFont(FONT_MONO, 8.2)
    subtitle_lines = wrap_text(subtitle, FONT_MONO, 8.2, CARD_WIDTH - 2 * padding)
    for line in subtitle_lines[:2]:
        c.drawString(title_x, title_y, line)
        title_y -= 10

    # Metrics
    metrics_top = title_y - 10
    for label, key in METRICS:
        value = getattr(row, key)
        c.setFillColor(ink_soft)
        c.setFont(FONT_DISPLAY, 8.0)
        c.drawString(title_x, metrics_top, label)
        c.setFillColor(ink)
        c.setFont(FONT_DISPLAY_BOLD, 9.0)
        c.drawRightString(x + CARD_WIDTH - padding, metrics_top, format_metric(value))
        c.setStrokeColor(colors.Color(0.07, 0.12, 0.16, alpha=0.18))
        c.setLineWidth(0.5)
        c.line(title_x, metrics_top - 4, x + CARD_WIDTH - padding, metrics_top - 4)
        metrics_top -= 13

    # Factoid box
    factoid_height = 56
    factoid_y = y + padding + 2
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
    card_border = hex_color("1f2326")
    accent = hex_color("ff8f2f")
    ink = hex_color("12202a")

    radius = 14
    padding = 12

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
    missing = [
        p for p in (DISPLAY_REGULAR, DISPLAY_BOLD, BODY_REGULAR, BODY_SEMIBOLD, BODY_ITALIC) if not p.exists()
    ]
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
    pdfmetrics.registerFont(TTFont(FONT_BODY_ITALIC, str(BODY_ITALIC)))


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
