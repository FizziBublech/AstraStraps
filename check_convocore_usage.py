#!/usr/bin/env python3
"""
Check Convocore agent & workspace token/credit usage for February 2026.
Queries the V3 API to investigate unexpected billing charges.

Usage:
    python3 check_convocore_usage.py
"""

import os
import requests
import json
from datetime import datetime, timezone

# --- Configuration ---
AGENT_ID = os.getenv("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
API_KEY = os.getenv("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.getenv("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")
WORKSPACE_UID = "qClnbTr3AcxFqSJ"

# February 2026 range
START_DATE = datetime(2026, 2, 1, tzinfo=timezone.utc)
END_DATE = datetime(2026, 2, 19, 23, 59, 59, tzinfo=timezone.utc)

START_MS = int(START_DATE.timestamp() * 1000)
END_MS = int(END_DATE.timestamp() * 1000)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def fetch_agent_usage():
    """Fetch agent-level credit/LLM usage."""
    url = f"{BASE_URL}/agents/{AGENT_ID}/usage"
    payload = {"range": {"start": START_MS, "end": END_MS}}

    print("📊 Agent Usage")
    print(f"   Agent ID: {AGENT_ID}")
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print(f"   Status:   {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"   Response: {json.dumps(data, indent=2, default=str)}")
        return data
    else:
        print(f"   Error:    {resp.text[:300]}")
        return None


def fetch_workspace_usage(page=1):
    """Fetch workspace-level usage statistics."""
    url = f"{BASE_URL}/workspaces/{WORKSPACE_UID}/usage"
    payload = {
        "range": {"start": START_MS, "end": END_MS},
        "logsPage": page,
    }

    print(f"\n🏢 Workspace Usage (page {page})")
    print(f"   Workspace UID: {WORKSPACE_UID}")
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print(f"   Status:        {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"   Response: {json.dumps(data, indent=2, default=str)}")
        return data
    else:
        print(f"   Error: {resp.text[:300]}")
        return None


def main():
    print("=" * 60)
    print("  Convocore Usage Check — February 2026")
    print(f"  Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"  Base URL: {BASE_URL}")
    print("=" * 60)
    print()

    agent_data = fetch_agent_usage()
    ws_data = fetch_workspace_usage()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)

    if agent_data:
        credits = agent_data.get("creditsConsumed", "N/A")
        print(f"  Agent credits consumed:    {credits}")
        metrics = agent_data.get("metrics", {})
        if metrics:
            print(f"  Agent metrics:             {json.dumps(metrics, default=str)}")
        else:
            print(f"  Agent metrics:             (empty)")

    if ws_data:
        km = ws_data.get("keyMetrics", {})
        print(f"  Workspace credits charged: {km.get('creditsCharged', 'N/A')}")
        print(f"  Workspace credits consumed:{km.get('creditsConsumed', 'N/A')}")
        llms = km.get("llms", [])
        print(f"  LLM models used:           {llms if llms else '(none)'}")
        agents_usage = km.get("agentsUsage", [])
        print(f"  Agents usage:              {agents_usage if agents_usage else '(none)'}")
        logs = ws_data.get("logs", [])
        print(f"  Usage logs:                {len(logs)} entries")
        for log in logs[:10]:
            print(f"    {json.dumps(log, default=str)}")
        charts = ws_data.get("charts", [])
        print(f"  Charts data:               {len(charts)} entries")

    print()
    if agent_data and ws_data:
        total = (agent_data.get("creditsConsumed", 0) or 0) + (km.get("creditsConsumed", 0) or 0)
        if total == 0:
            print("  ⚠️  RESULT: Both agent and workspace report 0 credits consumed.")
            print("     This contradicts 5x extra billing charges.")
            print("     Possible explanations:")
            print("     1. Billing charges may be for the subscription/plan, not usage")
            print("     2. Credits consumed via Agent Tester or other workspace features")
            print("     3. Knowledge base indexing/re-indexing charges")
            print("     4. Platform interaction fees not tracked at agent level")
            print()
            print("  👉 Recommended: Check the Convocore dashboard billing page directly")
            print("     or contact Convocore support with this data.")


if __name__ == "__main__":
    main()
