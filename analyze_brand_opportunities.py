import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time

load_dotenv()

REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN')
REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"

TARGET_CHANNELS = [
    'magic-shaper-shapewear', 
    'magic-shaper-uk', 
    'bottomdr', 
    'bodwellbeing'
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
    
    all_conversations = []
    page = 1
    
    # Fetch up to 3 pages (approx 90-100 items) to get a good recent sample
    while page <= 3:
        url = f"{REAMAZE_BASE_URL}/conversations"
        params = {
            'channel': slug, # Use channel instead of category
            'limit': 30,     # Default page size often 30
            'page': page
        }
        
        try:
            # print(f"Fetching page {page}...")
            response = requests.get(url, auth=auth, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Failed to fetch page {page}: {response.status_code}")
                break

            data = response.json()
            conversations = data.get('conversations', [])
            if not conversations:
                break
                
            all_conversations.extend(conversations)
            page += 1
            # respectful delay
            # time.sleep(0.2) 
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    if not all_conversations:
        print("No conversations found.")
        return

    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)
    last_90_days = now - timedelta(days=90)
    
    count_30 = 0
    count_90 = 0
    customer_ticket_count = 0
    
    topic_counts = {k: 0 for k in TOPIC_KEYWORDS.keys()}
    topic_counts['Other'] = 0
    
    recent_customer_subjects = []
    
    latest_date = None
    oldest_fetched_date = None

    for convo in all_conversations:
        created_at_str = convo.get('created_at')
        if not created_at_str:
            continue
            
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except:
            continue

        if latest_date is None or created_at > latest_date:
            latest_date = created_at
        if oldest_fetched_date is None or created_at < oldest_fetched_date:
            oldest_fetched_date = created_at
        
        # Date filtering
        is_recent_30 = created_at >= last_30_days
        is_recent_90 = created_at >= last_90_days
        
        if is_recent_30:
            count_30 += 1
        if is_recent_90:
            count_90 += 1
            
        # Subject Analysis
        subject = convo.get('subject', '').lower()
        body = convo.get('message', {}).get('body', '').lower()
        full_text = f"{subject} {body}"
        
        # Skip analysis for old tickets if we only care about recent trends? 
        # Let's analyze all fetched for better categorization sample
        
        # Categorize
        detected_topic = 'Other'
        
        # Check System/Admin first to exclude
        is_system = False
        for keyword in TOPIC_KEYWORDS['System/Admin']:
            if keyword in subject: # Strict subject check for system messages often better
                is_system = True
                break
        
        if is_system:
            topic_counts['System/Admin'] += 1
            continue # Don't count as customer ticket for detailed analysis
            
        customer_ticket_count += 1
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            if topic == 'System/Admin': continue
            for keyword in keywords:
                if keyword in full_text:
                    detected_topic = topic
                    break
            if detected_topic != 'Other':
                break
        
        topic_counts[detected_topic] += 1
        
        if is_recent_90 and len(recent_customer_subjects) < 10:
            recent_customer_subjects.append(f"[{detected_topic}] {convo.get('subject')}")

    print(f"Total Fetched: {len(all_conversations)}")
    if latest_date:
        print(f"Date Range: {latest_date.strftime('%Y-%m-%d')} to {oldest_fetched_date.strftime('%Y-%m-%d')}")
    
    print(f"\n--- Volume Stats ---")
    print(f"Total in Last 30 Days: {count_30}")
    print(f"Total in Last 90 Days: {count_90}")
    
    print(f"\n--- Topic Breakdown (All Fetched) ---")
    # Filter out System/Admin from percentages if desired, but good to show volume
    total_analyzed = len(all_conversations)
    if total_analyzed > 0:
        for topic, count in topic_counts.items():
            pct = (count / total_analyzed) * 100
            print(f"{topic}: {count} ({pct:.1f}%)")
            
    print(f"\n--- Recent Customer Ticket Sample (Last 90 Days) ---")
    if recent_customer_subjects:
        for subj in recent_customer_subjects:
            print(subj)
    else:
        print("No customer tickets found in last 90 days.")

if __name__ == "__main__":
    print(f"Starting analysis for: {', '.join(TARGET_CHANNELS)}")
    for channel in TARGET_CHANNELS:
        analyze_channel(channel)
