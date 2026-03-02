# Convocore Support Issue Draft

**Subject:** Discrepancy between Billing and Usage API (0 Credits Consumed vs 5x Extra Usage Charges)

Hi Convocore Team,

I am writing to report a significant discrepancy between the billing charges I'm receiving and the usage reported by your V3 API.

**Issue Summary:**
I have been billed **5 times this month (February 2026)** for "extra usage". This is unexpected because:

1. This bot handles only medium volume.
2. I am using my own API keys (BYOK) via OpenRouter.
3. **Your own V3 Usage API reports 0 credits consumed** for this period.

**Account Details:**

* **Workspace Email:** `alexander@freedommachine.eu`
* **Workspace UID:** `qClnbTr3AcxFqSJ`
* **Agent ID:** `QTbeXwvOediCAv2`

**Technical Verification:**
I queried your V3 API endpoints for the period **Feb 1, 2026 – Feb 19, 2026**, and both the Agent and Workspace endpoints confirm zero consumption.

**1. Agent Usage**
*Endpoint:* `POST /v3/agents/QTbeXwvOediCAv2/usage`
*Response:*

```json
{
  "creditsConsumed": 0,
  "metrics": {},
  "callMinutes": 0
}
```

**2. Workspace Usage**
*Endpoint:* `POST /v3/workspaces/qClnbTr3AcxFqSJ/usage`
*Response:*

```json
{
  "keyMetrics": {
    "creditsCharged": 0,
    "creditsConsumed": 0,
    "llms": [],
    "agentsUsage": []
  },
  "logs": []
}
```

Since your system's source of truth (the API) shows 0 credits consumed and 0 credits charged, these billing charges appear to be erroneous. Could you please investigate the source of these "extra usage" charges and refund the incorrect amounts?

Best regards,
Alexander
