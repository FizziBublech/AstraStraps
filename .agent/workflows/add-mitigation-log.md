---
description: Add a mitigation note to a specific issue in the tracker
---

This workflow allows you to programmatically add notes to an issue, optionally updating its status. This is useful for tracking fixes or investigation steps.

1. **Identify the Issue ID**
   - You can find the Issue ID on the [Dashboard](http://localhost:5000/dashboard) (e.g., `2tgVKPUrU1cYlIQ`).
   - Or checking the `issue_tracker.json` file.

2. **Run the mitigation script**
   Replace `ISSUE_ID` with the actual ID and provide your mitigation note.

   ```bash
   python log_mitigation.py --id ISSUE_ID --note "Describe what you did to fix or mitigate the issue"
   ```

   **Optional: Update Status**
   You can also update the status to `Resolved`, `Investigating`, etc.

   ```bash
   python log_mitigation.py --id ISSUE_ID --note "Fix deployed to prod" --status Resolved
   ```
