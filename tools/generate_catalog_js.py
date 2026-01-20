#!/usr/bin/env python3
"""
Generate tmp/catalog.js from data/catalog.csv.

Matches the format in data/catalog_template.js:
const euroCoinsCatalog=[{...}];
"""

import argparse
import csv
import json
from pathlib import Path


def parse_row(row: dict) -> dict:
    return {
        "type": row.get("type", ""),
        "year": int(row["year"]) if row.get("year") else "",
        "country": row.get("country", ""),
        "series": row.get("series", ""),
        "value": float(row["value"]) if row.get("value") else "",
        "id": row.get("id", ""),
        "image": row.get("image", ""),
        "feature": row.get("feature", ""),
        "volume": row.get("volume", ""),
    }


def generate_catalog_js(csv_path: Path, output_path: Path, const_name: str) -> None:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [parse_row(row) for row in reader]

    output = f"const {const_name}=" + json.dumps(rows, ensure_ascii=True, separators=(",", ":")) + ";"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate catalog.js from catalog CSV.")
    parser.add_argument(
        "--csv",
        default="data/catalog.csv",
        help="Path to catalog CSV file.",
    )
    parser.add_argument(
        "--out",
        default="tmp/catalog.js",
        help="Output JS file path.",
    )
    parser.add_argument(
        "--const-name",
        default="euroCoinsCatalog",
        help="Name of the catalog array constant.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    output_path = Path(args.out)
    generate_catalog_js(csv_path, output_path, args.const_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
