import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")

def fetch_conversations():
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/export?format=json"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

data = fetch_conversations()
convos = data.get('data', [])

november_convos = []
for convo in convos:
    ts = convo['metadata']['convo'].get('ts', 0)
    convo_date = datetime.fromtimestamp(ts).strftime('%Y-%m')
    if convo_date == '2025-11':
        november_convos.append(convo)

print(f"Total conversations in November 2025: {len(november_convos)}")
