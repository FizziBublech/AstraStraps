import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")

def test_fetch(params=None):
    print(f"Fetching with params: {params}")
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/export?format=json"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        convos = data.get('data', [])
        print(f"Returned {len(convos)} conversations")
        
        from collections import defaultdict
        daily_counts = defaultdict(int)
        
        for c in convos:
            ts = c['metadata']['convo'].get('ts', 0)
            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            daily_counts[date_str] += 1
            
        print("\nDaily Volume:")
        for date in sorted(daily_counts.keys(), reverse=True):
            if "2025-12" in date or "2026-01" in date:
                print(f"{date}: {daily_counts[date]}")
            
    except Exception as e:
        print(f"Error: {e}")

print("--- Volume Check ---")
test_fetch()
