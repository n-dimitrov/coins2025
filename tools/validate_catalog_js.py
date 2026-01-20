#!/usr/bin/env python3
"""
Validate and summarize a catalog.js file generated from catalog CSV.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


CATALOG_PATTERN = re.compile(r"\[\s*{.*}\s*\]\s*;?\s*$", re.DOTALL)


def load_catalog(js_path: Path) -> list:
    content = js_path.read_text(encoding="utf-8")
    match = CATALOG_PATTERN.search(content)
    if not match:
        raise ValueError("Could not find a JSON array in the catalog JS file.")
    json_text = match.group(0)
    if json_text.endswith(";"):
        json_text = json_text[:-1]
    return json.loads(json_text)


def summarize(catalog: list) -> str:
    total = len(catalog)
    type_counter = Counter(item.get("type", "") for item in catalog)
    country_counter = Counter(item.get("country", "") for item in catalog)

    by_country = defaultdict(Counter)
    for item in catalog:
        country = item.get("country", "")
        coin_type = item.get("type", "")
        by_country[country][coin_type] += 1
        by_country[country]["total"] += 1

    lines = []
    lines.append(f"Total coins: {total}")
    lines.append(f"Regular (RE): {type_counter.get('RE', 0)}")
    lines.append(f"Commemorative (CC): {type_counter.get('CC', 0)}")
    lines.append(f"Countries: {len([c for c in country_counter if c])}")
    lines.append("")
    lines.append("By country:")
    for country in sorted(country_counter):
        if not country:
            continue
        counts = by_country[country]
        line = (
            f"- {country}: total {counts.get('total', 0)}, "
            f"RE {counts.get('RE', 0)}, CC {counts.get('CC', 0)}"
        )
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate catalog.js and print stats.")
    parser.add_argument(
        "--js",
        default="tmp/catalog.js",
        help="Path to catalog.js file.",
    )
    args = parser.parse_args()

    catalog = load_catalog(Path(args.js))
    print(summarize(catalog))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
