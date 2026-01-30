import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")

def fetch_and_save_samples():
    print(f"Fetching last 10 conversations from {BASE_URL}...")
    
    # Fetching with page_size=10 to get just what we need
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/export?format=json&page_size=10"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        convos = data.get('data', [])
        print(f"Downloaded {len(convos)} conversations.")
        
        output_file = "sample_transcripts.json"
        with open(output_file, "w") as f:
            json.dump(convos, f, indent=2)
            
        print(f"Saved raw data to {output_file}")
        
        # Print a quick preview of the first one to check structure
        if convos:
            first = convos[0]
            print("\nStructure Preview (First Convo Keys):")
            print(first.keys())
            if 'turns' in first:
                print(f"Turns count: {len(first['turns'])}")
            elif 'messages' in first:
                print(f"Messages count: {len(first['messages'])}")
            else:
                print("Could not find 'turns' or 'messages' key. Please inspect file.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_save_samples()
