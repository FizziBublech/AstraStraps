import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

CHANNEL_SLUG = 'bottomdr'

def analyze_missed_calls():
    print(f"Analyzing missed calls for: {CHANNEL_SLUG}")
    auth = (REAMAZE_EMAIL, REAMAZE_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    # Fetch a batch of recent conversations
    url = f"{REAMAZE_BASE_URL}/conversations"
    params = {
        'channel': CHANNEL_SLUG,
        'limit': 30 
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        conversations = response.json().get('conversations', [])
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return

    missed_call_count = 0
    examples = []

    print("\nscanning subjects...")
    for convo in conversations:
        subject = convo.get('subject', '')
        body = convo.get('message', {}).get('body', '')
        
        # Check for keywords more broadly
        is_missed = 'missed call' in subject.lower() or 'voicemail' in subject.lower() or 'Call from' in subject
        
        # Check origin/type if available
        origin = convo.get('origin') # 9 is often VOIP/Phone
        
        if is_missed or origin == 9:
            missed_call_count += 1
            if len(examples) < 3:
                examples.append({
                    'subject': subject,
                    'body': body,
                    'origin': origin,
                    'data': convo.get('data')
                })

    print(f"Found {missed_call_count} potential call logs in {len(conversations)} tickets.")
    
    for i, ex in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Subject: {ex['subject']}")
        print(f"Body: {ex['body']}")
        print(f"Origin: {ex['origin']}")

if __name__ == "__main__":
    analyze_missed_calls()
