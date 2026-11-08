"""Regression and negative tests for official NAV extraction and feed formats."""
import json
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_cometa import ANCHORS, extract_monthly_quotes, parse_price, write_outputs


def realistic_fixture(*, omit=None, corrupt=None, duplicate=None):
    """Synthetic DOM matching official table: DATA, QUOTA, ANDP + return table."""
    rows = []
    for y in range(2005, 2027):
        for m in range(1, 13):
            if (y, m) < (2005, 4) or (y, m) > (2026, 9):
                continue
            if (y, m) == omit:
                continue
            value = ANCHORS.get((y, m), Decimal("20.123"))
            value_text = f"{value:.3f}".replace(".", ",")
            if (y, m) == corrupt:
                value_text = "NaN"
            line = f"<tr><td>{m:02d}/{y}</td><td>{value_text}</td><td>1.200.000</td></tr>"
            rows.append(line)
            if (y, m) == duplicate:
                rows.append(line)
    return ('<html><h1>Crescita</h1><table><thead><tr><th>DATA</th><th>QUOTA</th>'
            f'<th>ANDP</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
            '<table><tr><th>DATA</th><th>RENDIMENTO ANNUO</th><th>ANDP</th></tr>'
            '<tr><td>12/2025</td><td>7,32</td><td>100</td></tr></table></html>')


class TestParser(unittest.TestCase):
    def test_price_italian_decimal(self):
        self.assertEqual(parse_price("27,209"), Decimal("27.209"))
        self.assertEqual(parse_price("27.209"), Decimal("27.209"))
        for v in ("-27,209", "nan", "2e2", "0,6", "€ 0,5", ""):
            self.assertIsNone(parse_price(v), v)

    def test_actual_known_values_and_month_ends(self):
        rows = extract_monthly_quotes(realistic_fixture(), today=date(2026, 11, 8))
        self.assertEqual(len(rows), 258)
        self.assertEqual(rows[0], {"date": "2005-04-30", "close": 11.965})
        self.assertEqual(rows[-1], {"date": "2026-09-30", "close": 27.209})
        self.assertEqual([r for r in rows if r["date"] == "2026-08-31"][0]["close"], 27.4)

    def test_gap_rejected(self):
        with self.assertRaisesRegex(ValueError, "gap"):
            extract_monthly_quotes(realistic_fixture(omit=(2018, 11)), today=date(2026, 11, 8))

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            extract_monthly_quotes(realistic_fixture(duplicate=(2018, 11)), today=date(2026, 11, 8))

    def test_corrupt_quote_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid"):
            extract_monthly_quotes(realistic_fixture(corrupt=(2026, 9)), today=date(2026, 11, 8))

    def test_anchor_rejected(self):
        html = realistic_fixture().replace("27,209", "27,210")
        with self.assertRaisesRegex(ValueError, "integrity"):
            extract_monthly_quotes(html, today=date(2026, 11, 8))

    def test_wrong_table_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected one"):
            extract_monthly_quotes("<table><tr><td>DATA</td><td>ANDP</td></tr></table>")

    def test_stale_rejected(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            extract_monthly_quotes(realistic_fixture(), today=date(2027, 6, 1))

    def test_future_rejected(self):
        with self.assertRaisesRegex(ValueError, "Future"):
            extract_monthly_quotes(realistic_fixture(), today=date(2026, 8, 1))

    def test_files_and_status(self):
        rows = extract_monthly_quotes(realistic_fixture(), today=date(2026, 11, 8))
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            write_outputs(rows, target)
            json_file = json.loads((target / "cometa-crescita.json").read_text())
            metadata = json.loads((target / "status.json").read_text())
            csv_content = (target / "cometa-crescita.csv").read_text()
            self.assertEqual(json_file[-1], rows[-1])
            self.assertEqual(metadata["last_quote_eur"], 27.209)
            self.assertFalse(metadata["position_data_included"])
            self.assertIn("2026-09-30;27,209", csv_content)
            self.assertTrue((target / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
