---
description: Close out a month by remediating all issues and generating the monthly performance report.
---

// turbo-all

## Overview

This workflow closes out a calendar month for AstraStraps. It runs the full remediation pipeline for the month, then generates the polished monthly bot performance report.

Run this workflow at the start of a new month (e.g., run it in early February to close out January).

**Before starting:** Ask the user which month to close if not already specified. Format: `YYYY-MM` (e.g., `2026-01`).

---

## Step 1: Analyze Transcripts for the Month

Run the transcript analysis, scoped to the month being closed:

```bash
python3 analyze_transcripts.py --since-last
```

> Use `--since-last` for continuity. If you need to re-analyze a specific range, use `--from YYYY-MM-01 --to YYYY-MM-28` (adjust end date for the month).

---

## Step 2: Remediate Issues

Review the generated `analysis_report_*.json` file, then run remediation:

```bash
# Dry-run first to preview what will be deleted
python3 process_issues.py analysis_report_YYYYMMDD_HHMMSS.json --dry-run

# Run the actual remediation
python3 process_issues.py analysis_report_YYYYMMDD_HHMMSS.json
```

> Replace `YYYYMMDD_HHMMSS` with the timestamp of the latest report file generated in Step 1.

---

## Step 3: Backfill Categories

```bash
python3 backfill_categories.py
```

---

## Step 4: Download Full Transcripts & Extract Product Stats

Download the latest full transcripts from the Convocore API (needed for accurate product data):

```bash
python3 fetch_deep_sample.py
```

Then extract product recommendation stats for the month being closed:

```bash
python3 extract_product_stats.py --month YYYY-MM
```

> Replace `YYYY-MM` with the month being closed (e.g., `2026-01`).

---

## Step 5: Generate the Monthly Performance Report

```bash
python3 generate_monthly_report.py --month YYYY-MM
```

> Replace `YYYY-MM` with the month being closed.

---

## Step 6: Verify the Report

1. Start or verify the Flask server is running:

```bash
lsof -i :5000 || ./venv/bin/python3 main.py
```

1. Open the report in a browser:
   [http://localhost:5000/monthly-report/YYYY-MM](http://localhost:5000/monthly-report/YYYY-MM)

2. Check that:
   - Product Interest Leaderboard is populated with real product names (not generic terms)
   - Resolution Breakdown shows only "Resolved" and "Escalated"
   - The report looks correct on mobile (use browser DevTools to verify)

---

## Step 7: Share the Report

Present the final report link to the user:
`http://localhost:5000/monthly-report/YYYY-MM`
