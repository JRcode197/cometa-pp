#!/usr/bin/env python3
"""Export public Cometa Crescita monthly unit prices to Portfolio Performance.

Read-only access to the official public website: no credentials or investor data.
A failed download or validation never replaces a previously published feed.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import io
import json
import re
import time
import sys
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

SOURCE_URL = "https://www.cometafondo.it/andamenti/crescita/"
START_MONTH = (2005, 4)
MONTH_RE = re.compile(r"^\s*(0?[1-9]|1[0-2])\s*/\s*((?:19|20)\d{2})\s*$")
VALUE_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*(?:,\d{1,4})?$|^\d+(?:[,.]\d{1,4})?$", re.ASCII)
MAX_PAGE_BYTES = 3_000_000
# Historical observations to validate against the official source.
ANCHORS = {
    (2005, 4): Decimal("11.965"),
    (2025, 12): Decimal("25.686"),
    (2026, 8): Decimal("27.400"),
    (2026, 9): Decimal("27.209"),
}


def parse_price(raw: str) -> Decimal | None:
    """Parse an Italian NAV value; reject percentages, scientific notation, negatives."""
    s = raw.replace("\u00a0", "").replace("€", "").replace(" ", "").strip()
    if not VALUE_RE.fullmatch(s):
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        d = Decimal(s)
        return d if Decimal("1") < d < Decimal("1000") else None
    except InvalidOperation:
        return None


def month_end(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"


def extract_monthly_quotes(html: str, today: date | None = None) -> list[dict[str, object]]:
    """Find the unique DATA/QUOTA table; check coverage, freshness and anchors."""
    today = today or date.today()
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[dict[tuple[int, int], Decimal]] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        header = " ".join(c.get_text(" ", strip=True).upper() for row in rows[:3] for c in row.find_all(["th", "td"]))
        if not re.search(r"\bDATA\b", header) or not re.search(r"\bQUOTA\b", header):
            continue
        quotes: dict[tuple[int, int], Decimal] = {}
        for row in rows:
            cells = row.find_all(["td", "th"], recursive=False)
            if len(cells) < 2:
                continue
            matched = MONTH_RE.fullmatch(cells[0].get_text(" ", strip=True))
            if not matched:
                continue
            month, year = map(int, matched.groups())
            price = parse_price(cells[1].get_text(" ", strip=True))
            if price is None:
                raise ValueError(f"Invalid quote for {year:04d}-{month:02d}")
            key = (year, month)
            if key in quotes:
                raise ValueError(f"Duplicate monthly quote for {year:04d}-{month:02d}")
            quotes[key] = price
        if quotes:
            candidates.append(quotes)
    if len(candidates) != 1:
        raise ValueError(f"Expected one official DATA/QUOTA table; found {len(candidates)}")
    quotes = candidates[0]
    if min(quotes) != START_MONTH:
        raise ValueError(f"Historical series does not start at 04/2005: {min(quotes)}")
    keys = sorted(quotes)
    for (y1, m1), (y2, m2) in zip(keys, keys[1:]):
        if (y2 * 12 + m2) - (y1 * 12 + m1) != 1:
            raise ValueError(f"Historical gap between {y1}-{m1:02d} and {y2}-{m2:02d}")
    for key, expected in ANCHORS.items():
        if quotes.get(key) != expected:
            raise ValueError(f"Official integrity check failed for {key[0]}-{key[1]:02d}: {quotes.get(key)}")
    newest_year, newest_month = keys[-1]
    newest_end = date.fromisoformat(month_end(newest_year, newest_month))
    if newest_end > today:
        raise ValueError("Future-dated quote, refusing to publish")
    if (today - newest_end).days > 150:
        raise ValueError(f"Official quote is unexpectedly stale ({newest_end})")
    return [{"date": month_end(y, m), "close": float(quotes[(y, m)])} for y, m in keys]


def download_html() -> str:
    """Fetch public HTML, retrying only transient network/server failures."""
    req = Request(SOURCE_URL, headers={
        "User-Agent": "Mozilla/5.0 (compatible; public-cometa-crescita-feed/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    })
    for attempt in range(3):
        try:
            with urlopen(req, timeout=25) as response:
                final_url = urlparse(response.geturl())
                if final_url.scheme != "https" or final_url.netloc != "www.cometafondo.it":
                    raise ValueError("Unexpected redirect away from official Cometa website")
                raw = response.read(MAX_PAGE_BYTES + 1)
                if len(raw) > MAX_PAGE_BYTES:
                    raise ValueError("Source HTML unexpectedly large")
                if "html" not in response.headers.get("Content-Type", "text/html").lower():
                    raise ValueError("Source returned something other than HTML")
                return raw.decode("utf-8", errors="strict")
        except HTTPError as exc:
            if not (exc.code == 429 or 500 <= exc.code < 600) or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def write_outputs(quotes: list[dict[str, object]], outdir: Path) -> None:
    """Write files only after complete source validation."""
    outdir.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(quotes, ensure_ascii=False, indent=2) + "\n"
    csv_buf = io.StringIO(newline="")
    writer = csv.writer(csv_buf, delimiter=";")
    writer.writerow(["Date", "Quote"])
    for item in quotes:
        writer.writerow([item["date"], f"{item['close']:.3f}".replace(".", ",")])
    latest = quotes[-1]
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    status = {
        "source": SOURCE_URL,
        "generated_at_utc": timestamp,
        "number_of_months": len(quotes),
        "last_quote_date": latest["date"],
        "last_quote_eur": latest["close"],
        "prices_frequency": "monthly",
        "position_data_included": False,
    }
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cometa Crescita - quotazioni ufficiali</title></head>
    <body><h1>Cometa Crescita</h1><p>Fonte: <a href="{SOURCE_URL}">Fondo Cometa</a>.</p>
    <p>Ultima quota: {latest['close']:.3f} EUR ({latest['date']}).</p>
    <p>Dati mensili: {len(quotes)}. Generato il {timestamp}.</p>
    <ul><li><a href="cometa-crescita.json">Feed JSON Portfolio Performance</a></li>
    <li><a href="cometa-crescita.csv">Storico CSV</a></li>
    <li><a href="status.json">Metadati e aggiornamento</a></li></ul></body></html>\n"""
    outputs = {
        "cometa-crescita.json": json_text,
        "cometa-crescita.csv": csv_buf.getvalue(),
        "status.json": json.dumps(status, indent=2) + "\n",
        "index.html": html,
    }
    with tempfile.TemporaryDirectory(prefix=".cometa-nav-", dir=outdir) as tmp:
        for filename, content in outputs.items():
            Path(tmp, filename).write_text(content, encoding="utf-8")
        for filename in outputs:
            Path(tmp, filename).replace(outdir / filename)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, default=Path("site"))
    ap.add_argument("--html-fixture", type=Path, help="Use saved HTML for tests instead of network")
    args = ap.parse_args()
    html = args.html_fixture.read_text(encoding="utf-8") if args.html_fixture else download_html()
    quotes = extract_monthly_quotes(html)
    write_outputs(quotes, args.outdir)
    latest = quotes[-1]
    print(f"OK: {len(quotes)} months; {latest['date']} = {latest['close']:.3f} EUR")
    print(f"Source: {SOURCE_URL}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, UnicodeError, URLError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
