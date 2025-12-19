---
description: Run daily transcript analysis to identify technical errors and unhappy customers
---

// turbo-all

1. Ensure the virtual environment is activated and dependencies are installed.
2. Run the analysis script (defaults to today):

```bash
python3 analyze_transcripts.py
```

3. To analyze a specific date or limit the results:

```bash
# Analyze a specific date
python3 analyze_transcripts.py --date 2025-12-16

# Limit to first 5 conversations
python3 analyze_transcripts.py --limit 5
```

4. Check the console for the summary and look for the generated `analysis_report_YYYY-MM-DD_HHMMSS.json` file for detailed results.
