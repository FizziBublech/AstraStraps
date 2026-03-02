import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

# Use category as it worked in verify_content.py
CATEGORY_SLUG = 'bottomdr'

def analyze_missed_calls():
    print(f"Analyzing missed calls for category: {CATEGORY_SLUG}")
    auth = (REAMAZE_EMAIL, REAMAZE_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    url = f"{REAMAZE_BASE_URL}/conversations"
    params = {
        'category': CATEGORY_SLUG,
        'limit': 50 
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        conversations = response.json().get('conversations', [])
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return

    if not conversations:
        print("No conversations found.")
        return

    total_count = len(conversations)
    missed_call_count = 0
    voicemail_count = 0
    examples = []

    for convo in conversations:
        subject = convo.get('subject', '')
        # Check for specific patterns seen in previous output
        is_missed = 'missed call' in subject.lower()
        is_voicemail = 'voicemail' in subject.lower() or 'voice mail' in subject.lower()
        
        if is_missed:
            missed_call_count += 1
        if is_voicemail:
            voicemail_count += 1
            
        if (is_missed or is_voicemail) and len(examples) < 3:
            examples.append({
                'subject': subject,
                'body': convo.get('message', {}).get('body', ''),
                'sender': convo.get('message', {}).get('sender', {}),
                'created_at': convo.get('created_at')
            })

    call_logs_total = missed_call_count + voicemail_count
    proportion = (call_logs_total / total_count) * 100 if total_count > 0 else 0

    print(f"\n--- Statistics (Sample Size: {total_count}) ---")
    print(f"Missed Calls: {missed_call_count}")
    print(f"Voicemails: {voicemail_count}")
    print(f"Total Call Logs: {call_logs_total}")
    print(f"Proportion: {proportion:.1f}%")

    print(f"\n--- Examples ---")
    for i, ex in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Date: {ex['created_at']}")
        print(f"Subject: {ex['subject']}")
        print(f"Body: {ex['body']}") # Let's see if there's a recording link or text

if __name__ == "__main__":
    analyze_missed_calls()
