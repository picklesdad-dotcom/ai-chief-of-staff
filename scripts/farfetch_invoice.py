#!/usr/bin/env python3
"""Generate the monthly Farfetch invoice PDF (J&M Helltown, LLC / Greyscale Provincetown).

Example (October 2026 PO):
    python3 scripts/farfetch_invoice.py --inv 1145 --date 11/07/2026 --po FUS-000610-1 \
        --line Services Sales 4183.77 --line Returns Returns -136.00 --total 4047.77

- Due date defaults to invoice date + 30 days (net 30).
- One --line per PO line: Supplier's Price Bid Ask -> "Services Sales <amt>",
  Supplier's Return Bid Ask -> "Returns Returns <negative amt>".
- Exits with an error (and writes nothing) if the lines don't sum to --total.
"""
import argparse
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


def money(d: Decimal) -> str:
    s = f"${abs(d):,.2f}"
    return f"-{s}" if d < 0 else s


def build(inv_no, inv_date, due_date, po_no, lines, total, out):
    H = 792
    c = canvas.Canvas(str(out), pagesize=(612, 792))
    c.setTitle(f"Invoice #{inv_no}")
    c.setAuthor("J&M Helltown, LLC")
    dark, grey, line = HexColor("#222222"), HexColor("#666666"), HexColor("#cccccc")
    R, B = "Helvetica", "Helvetica-Bold"

    def t(x, top, s, f=R, sz=9, col=dark, right=False):
        c.setFont(f, sz)
        c.setFillColor(col)
        y = H - top - sz * 0.8
        (c.drawRightString if right else c.drawString)(x, y, s)

    t(32.2, 32.7, "INVOICE", B, 12)
    for top, s, f in [(47.9, "J&M Helltown, LLC", B), (59.2, "347 Commercial St", R),
                      (70.4, "Provincetown, MA 02657-2202", R)]:
        t(32.2, top, s, f, 7.5, grey if f == R else dark)
    t(174.4, 47.2, "Admin@greyscaleptown.com", R, 7.5, grey)
    t(174.4, 58.4, "+1 (253) 222-5041", R, 7.5, grey)

    for x in (32.2, 397.2):
        t(x, 134.9, "Bill to" if x < 100 else "Ship to", B, 7.5)
        for top, s in [(147.3, "Farfetch.com US LLC"), (160.8, "2301 East 7th Street A-250"),
                       (174.3, "Los Angeles, CA 90023 USA")]:
            t(x, top, s, R, 9)

    c.setStrokeColor(line)
    c.setDash(2, 2)
    c.setLineWidth(0.5)
    c.line(32, H - 222, 580, H - 222)
    c.setDash()

    t(32.2, 244.8, "Invoice details", B, 9)
    t(32.2, 259.8, f"Invoice no.: #{inv_no}")
    t(32.2, 273.3, f"Invoice date: {inv_date}")
    t(32.2, 286.8, f"Due date: {due_date}")

    t(27, 335.6, "#", B, 8)
    t(45.7, 337.1, "Product or service")
    t(207.6, 337.1, "Description")
    t(421.5, 337.1, "Qty")
    t(485.6, 337.1, "Rate")
    t(534, 337.1, "Amount")
    c.setStrokeColor(line)
    c.setLineWidth(0.7)
    c.line(45, H - 354.5, 567, H - 354.5)

    row_top = 364.8
    for i, (svc, desc, amt) in enumerate(lines, 1):
        a = money(amt)
        t(27, row_top, f"{i}.", R, 8)
        t(45, row_top, svc, B, 8)
        t(206.8, row_top, desc, R, 8, grey)
        t(432, row_top, "1", R, 8, grey)
        t(468.3, row_top, a, R, 8, grey)
        t(531, row_top, a, R, 8, grey)
        c.line(45 if i == 1 else 27, H - (row_top + 17.2), 567, H - (row_top + 17.2))
        row_top += 25.2

    base = row_top - 25.2 + 17.2  # y of last hairline; lower block follows the rows
    t(45, base + 22.7, "Ways to pay", B, 12)
    c.rect(46, H - (base + 60), 24.5, 15, stroke=1, fill=0)
    t(50, base + 48, "BANK", B, 5.5)
    t(45, base + 63, f"PO #{po_no}", R, 8)
    t(371.8, base + 13.6, "Total", B, 8)
    t(567, base + 12.2, money(total), B, 12, right=True)
    c.line(372, H - (base + 33.5), 567, H - (base + 33.5))
    c.save()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inv", required=True, help="Invoice number, e.g. 1146")
    p.add_argument("--date", default=datetime.now().strftime("%m/%d/%Y"), help="Invoice date MM/DD/YYYY (default today)")
    p.add_argument("--due", help="Due date MM/DD/YYYY (default invoice date + 30 days)")
    p.add_argument("--po", required=True, help="PO number exactly as on the PO, e.g. FUS-000610-1")
    p.add_argument("--line", nargs=3, action="append", required=True, metavar=("SERVICE", "DESC", "AMOUNT"))
    p.add_argument("--total", required=True, help="PO Total, e.g. 4047.77")
    p.add_argument("--outdir", default=".", help="Folder for the PDF")
    a = p.parse_args()

    inv_dt = datetime.strptime(a.date, "%m/%d/%Y")
    due = a.due or (inv_dt + timedelta(days=30)).strftime("%m/%d/%Y")
    lines = [(s, d, Decimal(amt.replace("$", "").replace(",", ""))) for s, d, amt in a.line]
    total = Decimal(a.total.replace("$", "").replace(",", ""))

    line_sum = sum(x[2] for x in lines)
    if line_sum != total:
        sys.exit(f"CHECK FAILED: lines sum to {money(line_sum)} but PO total is {money(total)}. No PDF written.")
    if not a.inv.isdigit():
        sys.exit("CHECK FAILED: invoice number should be digits only, e.g. 1146")

    out = Path(a.outdir) / f"Invoice__{a.inv}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    build(a.inv, a.date, due, a.po, lines, total, out)
    print(f"OK {out}  invoice #{a.inv}  date {a.date}  due {due}  PO #{a.po}  total {money(total)}  lines sum {money(line_sum)}")


if __name__ == "__main__":
    main()
