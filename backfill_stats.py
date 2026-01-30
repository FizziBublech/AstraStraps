import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")
STATS_FILE = "daily_stats.json"

def fetch_conversations():
    print("Fetching all conversations from Convocore...")
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/export?format=json"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

def main():
    data = fetch_conversations()
    if not data or 'data' not in data:
        print("No data found.")
        return

    convos = data['data']
    print(f"Found {len(convos)} total conversations.")

    stats = {}
    
    # Load existing if any, though we are likely overwriting/merging
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
        except:
            pass

    for convo in convos:
        ts = convo['metadata']['convo'].get('ts', 0)
        dt_obj = datetime.fromtimestamp(ts)
        date_str = dt_obj.strftime('%Y-%m-%d')
        convo_id = convo['metadata']['convo']['id']

        if date_str not in stats:
            stats[date_str] = []
        
        if convo_id not in stats[date_str]:
            stats[date_str].append(convo_id)

    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\nDaily Stats Summary:")
    for date, ids in sorted(stats.items()):
        print(f"{date}: {len(ids)} conversations")
        
    print(f"\nSaved to {STATS_FILE}")

if __name__ == "__main__":
    main()
