---
description: Categorize, log, and delete problematic conversations identified during analysis.
---

// turbo-all

1. Analyze new conversations (defaults to "since last run" for continuity):

```bash
python3 analyze_transcripts.py --since-last
```

1. Run the remediation script using the latest generated analysis report:

```bash
# Perform a dry-run first to see what will be deleted
python3 process_issues.py analysis_report_YYYYMMDD_HHMMSS.json --dry-run

# Run the actual remediation
python3 process_issues.py analysis_report_YYYYMMDD_HHMMSS.json
```

1. Run the backfill script to categorize and tag new issues:

```bash
python3 backfill_categories.py
```

1. Start or verify the dashboard server is running:

```bash
# Check if server is on port 5000, start if not
lsof -i :5000 || ./venv/bin/python3 main.py
```

1. **CRITICAL**: Always present the dashboard link after completing the steps above:
   Open [http://localhost:5000/dashboard](http://localhost:5000/dashboard) to view/address the issues.
