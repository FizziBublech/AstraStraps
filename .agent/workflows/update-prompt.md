---
description: How to update the AstraBot prompt with versioning
---

# Update AstraBot Prompt

This workflow describes how to safely update the bot's system instructions (prompt) using the automated versioning script.

## 1. Edit the Prompt

Modify the `updated_astrabot_prompt.md` file with your changes. ensuring you follow the request JSON structure and guidelines.

## 2. (Optional) Validate JSON

If you made changes to the JSON schemas within the prompt, double-check them for validity.

## 3. Run Dry-Run

Before pushing changes, run the script in dry-run mode to verify what will happen:

```bash
python3 update_bot_prompt.py --dry-run
```

## 4. Deploy Update

To push the changes to the live agent and save the version:

```bash
python3 update_bot_prompt.py
```

You can also add a message and author:

```bash
python3 update_bot_prompt.py --message "Fixed refund instructions" --author "Alex"
```

You can specified a specific agent ID (e.g. for testing) using the `--agent-id` flag:

```bash
python3 update_bot_prompt.py --agent-id QTbeXwvOediCAv2 --dry-run
```

## 5. Rollback (Manual)

If you need to rollback:

1. Check `prompts/history.json` or `prompts/archive/` for the version you want.
2. Copy the content of that version file back to `updated_astrabot_prompt.md`.
3. Run the update script again to "roll forward" to the old version.
