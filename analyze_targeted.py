import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

# Targeted run for missed channels
TARGET_CHANNELS = [
    'magic-shaper-shapewear', 
    'bottomdr'
]

TOPIC_KEYWORDS = {
    'Order Status': ['where', 'track', 'status', 'received', 'shipping', 'delivery', 'arrive', 'package', 'order'],
    'Returns/Refunds': ['return', 'refund', 'exchange', 'cancel', 'money back'],
    'Product Info': ['size', 'measurements', 'fit', 'material', 'color', 'stock', 'restock'],
    'System/Admin': ['payout', 'google ads', 'tiktok', 'collaboration', 'partnership', 'invoice', 'payment']
}

def analyze_channel(slug):
    print(f"\n{'='*40}")
    print(f"Analyzing Channel: {slug}")
    print(f"{'='*40}")
    
    auth = (REAMAZE_EMAIL, REAMAZE_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    # Just fetch top 50
    url = f"{REAMAZE_BASE_URL}/conversations"
    params = {'channel': slug, 'limit': 50}
    
    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        conversations = response.json().get('conversations', [])
    except Exception as e:
        print(f"Error: {e}")
        return

    if not conversations:
        print("No conversations.")
        return

    topic_counts = {k: 0 for k in TOPIC_KEYWORDS.keys()}
    topic_counts['Other'] = 0
    samples = []

    for convo in conversations:
        subject = convo.get('subject', '').lower()
        body = convo.get('message', {}).get('body', '').lower()
        full_text = f"{subject} {body}"
        
        detected_topic = 'Other'
        for topic, keywords in TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in full_text:
                    detected_topic = topic
                    break
            if detected_topic != 'Other': break
        
        topic_counts[detected_topic] += 1
        if len(samples) < 5:
            samples.append(f"[{detected_topic}] {convo.get('subject')}")

    # Output stats
    print(f"Sample Size: {len(conversations)}")
    for topic, count in topic_counts.items():
        if count > 0:
            print(f"{topic}: {count}")
            
    print("\nSample Subjects:")
    for s in samples:
        print(s)

if __name__ == "__main__":
    for c in TARGET_CHANNELS:
        analyze_channel(c)
