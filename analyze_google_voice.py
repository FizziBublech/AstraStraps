import os
import requests
from dotenv import load_dotenv
import json
import re

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

CATEGORY_SLUG = 'bottomdr'

def analyze_google_voice():
    print(f"Analyzing Google Voice emails for: {CATEGORY_SLUG}")
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

    gv_emails = []
    
    print("\n--- Examining Google Voice Email Content ---")
    for convo in conversations:
        subject = convo.get('subject', '')
        # Filter for Google Voice
        if 'missed call' in subject.lower() or 'voicemail' in subject.lower() or 'voice.google.com' in convo.get('message', {}).get('body', ''):
            body = convo.get('message', {}).get('body', '')
            gv_emails.append(body)
            
            # Look for specific markers
            is_voicemail = 'transcript' in body.lower() or 'play message' in body.lower()
            sent_to = convo.get('message', {}).get('recipient', {}).get('email')
            
            # Print snippets to identify version/type
            print(f"\nSubject: {subject}")
            if "Standard rates apply" in body:
                print("Marker: 'Standard rates apply' found (Typical of consumer/free version)")
            if "Google Workspace" in body:
                print("Marker: 'Google Workspace' found (Business version)")
            
            # Check for voicemail transcript
            if is_voicemail:
                print("Type: Voicemail with Transcript potential")
                # Try to extract transcript snippet - often it's in the body even if not labeled "Transcript:"
                # Look for the block of text that isn't the footer
                match = re.search(r'Transcript:(.+?)(?:Play message|to listen to this message|Google LLC)', body, re.DOTALL | re.IGNORECASE)
                if match:
                    print(f"Transcript Snippet: {match.group(1).strip()}")
                else:
                    # Fallback: Just print the first few lines of body to see what's there
                    print(f"Body Preview: {body[:300]}")
            else:
                print("Type: Missed Call Notification only")

    print(f"\nTotal Google Voice Emails Analyzed: {len(gv_emails)}")

if __name__ == "__main__":
    analyze_google_voice()
