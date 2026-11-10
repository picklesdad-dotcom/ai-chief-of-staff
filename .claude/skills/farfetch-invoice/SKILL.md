---
name: farfetch-invoice
description: Monthly Farfetch invoice. Takes the uploaded Farfetch PO PDF, builds Invoice__<n>.pdf, runs checks, emails it to Admin@greyscaleptown.com for Michael to review and forward. Never emails Farfetch directly.
user_invocable: true
---

Monthly Farfetch invoice for J&M Helltown, LLC (Greyscale Provincetown). Go one step at a time and confirm each step before moving on.

## Hard rules

- **Never send anything to Farfetch.** The only email Claude sends is to `Admin@greyscaleptown.com`. Michael reviews it and forwards it to `invoices+partners@farfetch.coupahost.com`.
- Never invent a PO number, total, or invoice number. If a value can't be read from the PO or the log, ask.
- If any check fails, stop and tell Michael. Do not send.

## Step 1: Get the PO

Farfetch POs are downloaded from the Farfetch partner portal (they are not emailed). If no PO PDF has been uploaded in this session, ask Michael to download the PO from the portal and upload it here. Wait.

Read the PO (use the pdf skill or `pdftotext -layout`). Extract:
- **Number** (e.g. `FUS-000610-1`, keep the `-1` suffix exactly)
- Line items: "Supplier's Price Bid Ask" (BA003) and "Supplier's Return Bid Ask" (BA004, negative)
- **Total**

## Step 2: Work out the invoice number

1. Read `.claude/memory/project_farfetch_invoices.md` for the last invoice number.
2. Cross-check Gmail: search `in:sent to:Admin@greyscaleptown.com subject:"Farfetch Invoice"` for the highest invoice number already sent. Scheduled sessions may not have the latest log, so Gmail wins if it is higher.
3. Next number = highest found + 1. Tell Michael the number and ask him to confirm the prior invoice was sent (and paid, if he knows).
4. If this PO number already appears on an earlier invoice in the log or Gmail, stop and ask. It may be a duplicate.

## Step 3: Build the PDF

```
python3 scripts/farfetch_invoice.py --inv <n> --po <PO number> \
  --line Services Sales <sales amount> \
  --line Returns Returns <negative returns amount> \
  --total <PO total> --outdir <scratchpad>
```
- Drop the Returns line if the PO has only one line.
- Invoice date defaults to today; due date is +30 days automatically.
- The script refuses to write the PDF if the lines don't sum to the total.

## Step 4: Check it

1. Lines sum to the PO total (the script enforces this; confirm the printed totals).
2. PO number on the invoice matches the PO exactly, including the suffix.
3. Invoice number is the previous one + 1.
4. Render it (`pdftoppm -png -r 110`) and look at the image before sending.
5. Compare to last month's total in the log. If it differs by more than about 50%, flag it and ask whether anything from an earlier PO is still open.

Show Michael the rendered preview and a one-line summary (invoice #, PO #, total, due date). Ask: "Send to Admin@greyscaleptown.com for your review?" Wait for yes.

## Step 5: Email it to Admin

Use Gmail `send_message` with the PDF attached (base64, `application/pdf`, filename `Invoice__<n>.pdf`).

- **To:** Admin@greyscaleptown.com
- **Subject:** `Farfetch Invoice #<n> - J&M Helltown, LLC - PO #<PO number>`
- **Body** (written so Michael can forward it to Farfetch as-is; precise, no filler):

```
Hello,

Attached is Invoice #<n> from J&M Helltown, LLC for PO #<PO number>.

Invoice total: <total>
Invoice date: <date>
Due date: <due date>

Thank you,
J&M Helltown, LLC
Admin@greyscaleptown.com
+1 (253) 222-5041
```

## Step 6: Log it and remind

1. Add a row to `.claude/memory/project_farfetch_invoices.md` (sent to Farfetch = "pending forward") and bump "Next invoice number". Commit and push.
2. Tell Michael:
   - "Forward the email in the Admin inbox to **invoices+partners@farfetch.coupahost.com** by the **12th**, or payment slips a month."
   - When he confirms he forwarded it, mark it "yes" in the log.
