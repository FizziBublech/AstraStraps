import os
import requests
from dotenv import load_dotenv

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

CHANNELS = ['magic-shaper-shapewear', 'bottomdr']

def check(slug):
    print(f"Checking {slug} with 'category' param...")
    auth = (REAMAZE_EMAIL, REAMAZE_API_TOKEN)
    url = f"{REAMAZE_BASE_URL}/conversations"
    params = {'category': slug, 'limit': 5} # Using category as per channel_stats.py success
    
    res = requests.get(url, auth=auth, params=params)
    data = res.json()
    convos = data.get('conversations', [])
    
    print(f"Got {len(convos)} convos.")
    for c in convos:
        print(f"- [{c.get('category', {}).get('slug')}] {c.get('subject')}")

if __name__ == "__main__":
    for c in CHANNELS:
        check(c)
