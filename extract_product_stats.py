import json
import re
from collections import Counter
from datetime import datetime
import argparse

def extract_stats(month_str=None):
    # Default to current month/prev month logic or passed arg
    target_month = month_str if month_str else "2026-01"
    
    print(f"Extracting product stats for: {target_month}")
    
    try:
        with open('sample_transcripts.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("sample_transcripts.json not found. Please run fetch_deep_sample.py first.")
        return {}

    product_counter = Counter()
    
    for convo in data:
        # Check date
        ts = convo['metadata']['convo'].get('ts', 0)
        dt = datetime.fromtimestamp(ts)
        str_date = dt.strftime("%Y-%m")
        
        if str_date != target_month:
            continue
            
        if 'turns' not in convo: continue
        
        for turn in convo['turns']:
            for msg in turn.get('messages', []):
                # Look for tool outputs
                if msg.get('type') == 'debug:tell':
                    payload = msg.get('payload', {})
                    message_text = payload.get('message', '')
                    
                    if "Tool ended: recommend_products" in message_text:
                        # Use regex to find titles
                        titles = re.findall(r'"title":"(.*?)"', message_text)
                        for title in titles:
                            # CLEANING LOGIC
                            # 1. Remove variant specs like " / 38MM"
                            clean_title = title.split(" / ")[0]
                            # 2. Remove trailing dashes often found in Shopify handles if they appear
                            clean_title = clean_title.split(" - ")[0]
                            
                            # 3. Consolidate specific known fragments if they are split
                            if "Neptuse" in clean_title: clean_title = "Neptuse Silicone Band"
                            if "Nix" in clean_title: clean_title = "Nix Nylon Band"
                            if "Oscen" in clean_title: clean_title = "Oscen Sports Band"
                            
                            product_counter[clean_title] += 1
                            
    # Save to file
    output = {
        "month": target_month,
        "product_counts": dict(product_counter)
    }
    
    filename = f"product_stats_{target_month}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"Saved {len(product_counter)} product stats to {filename}")
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", help="YYYY-MM", default="2026-01")
    args = parser.parse_args()
    
    extract_stats(args.month)
