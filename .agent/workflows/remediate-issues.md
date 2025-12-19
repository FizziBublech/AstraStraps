---
description: Categorize, log, and delete problematic conversations identified during analysis.
---

// turbo-all

1. Ensure you have an analysis report generated from `analyze_transcripts.py`.
2. Run the remediation script to log issues and delete technical errors from the Convocore frontend (Note: sentiment-only issues are logged but NOT deleted):

```bash
# Perform a dry-run first to see what will be deleted
python3 process_issues.py analysis_report_YYYY-MM-DD_HHMMSS.json --dry-run

# Run the actual remediation
python3 process_issues.py analysis_report_YYYY-MM-DD_HHMMSS.json
```

3. Open `issue_dashboard.html` in your browser to view the logged issues and their status.
4. Address the technical errors or customer complaints identified in the dashboard.
