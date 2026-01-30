---
description: Run daily transcript analysis to identify technical errors and unhappy customers
---

// turbo-all

1. Ensure the virtual environment is activated and dependencies are installed.
2. Run the analysis script (defaults to today, or incremental if specified):

```bash
# Analyze everything since the last successful run
python3 analyze_transcripts.py --since-last

# Analyze today (default if no flag provided)
python3 analyze_transcripts.py
```

1. To analyze a specific date or limit the results:

```bash
# Analyze a specific date
python3 analyze_transcripts.py --date 2025-12-16

# Analyze a range
python3 analyze_transcripts.py --start-date 2026-01-01 --end-date 2026-01-05

# Adjust limit (current default is 100)
python3 analyze_transcripts.py --limit 500
```

1. Check the console for the summary and look for the generated `analysis_report_YYYY-MM-DD_HHMMSS.json` file for detailed results.
