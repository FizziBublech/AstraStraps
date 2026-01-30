import json
import re
from collections import Counter

def analyze_transcripts():
    try:
        with open('sample_transcripts.json', 'r') as f:
            data = json.load(f)
            
        print(f"Analyzing {len(data)} conversations...")
        
        product_counter = Counter()
        recs_found = 0
        
        for convo in data:
            if 'turns' not in convo: continue
            
            for turn in convo['turns']:
                for msg in turn.get('messages', []):
                    # Look for tool outputs
                    if msg.get('type') == 'debug:tell':
                        payload = msg.get('payload', {})
                        message_text = payload.get('message', '')
                        
                        if "Tool ended: recommend_products" in message_text:
                            # Use regex to find titles, much more robust against truncated JSON
                            titles = re.findall(r'"title":"(.*?)"', message_text)
                            for title in titles:
                                product_counter[title] += 1
                                recs_found += 1

                                
        print(f"\nFound {recs_found} specific product recommendations.")
        print("\nTop Recommended Products:")
        for product, count in product_counter.most_common(20):
            print(f"- {product}: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_transcripts()
