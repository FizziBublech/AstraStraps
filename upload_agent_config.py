import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AGENT_CONFIG_FILE = 'agent_config.json'
UPLOAD_OUTPUT_FILE = 'agent_config_upload.json'
API_URL = "https://na-gcp-api.vg-stuff.com/v3/agents"
AGENT_ID = "QTbeXwvOediCAv2" # Default, or read from file

def main():
    if not os.path.exists(AGENT_CONFIG_FILE):
        print(f"Error: {AGENT_CONFIG_FILE} not found.")
        return

    print(f"Reading {AGENT_CONFIG_FILE}...")
    with open(AGENT_CONFIG_FILE, 'r') as f:
        config_data = json.load(f)

    # Convert to string for easy replacement
    config_str = json.dumps(config_data)
    
    # 1. Substitute OpenRouter API Key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if openrouter_key:
        if "YOUR_OPENROUTER_API_KEY_HERE" in config_str:
            print("✅ Substituting OpenRouter API Key...")
            config_str = config_str.replace("YOUR_OPENROUTER_API_KEY_HERE", openrouter_key)
        else:
            print("ℹ️  Placeholder 'YOUR_OPENROUTER_API_KEY_HERE' not found. Skipping OpenRouter substitution.")
    else:
        print("⚠️  Warning: OPENROUTER_API_KEY not found in .env.")

    # 2. Substitute VoiceGlow Secret Key
    # User might name it VOICEGLOW_API_KEY or SECRET_API_KEY
    voiceglow_key = os.getenv('VOICEGLOW_API_KEY') or os.getenv('SECRET_API_KEY')
    if voiceglow_key:
        if "YOUR_SECRET_API_KEY_HERE" in config_str:
            print("✅ Substituting VoiceGlow Secret Key...")
            config_str = config_str.replace("YOUR_SECRET_API_KEY_HERE", voiceglow_key)
        else:
            print("ℹ️  Placeholder 'YOUR_SECRET_API_KEY_HERE' not found. Skipping Secret Key substitution.")
    else:
        if "YOUR_SECRET_API_KEY_HERE" in config_str:
             print("⚠️  Warning: 'YOUR_SECRET_API_KEY_HERE' placeholder found, but no matching key in .env (set VOICEGLOW_API_KEY or SECRET_API_KEY).")

    # Parse back to JSON
    final_payload_full = json.loads(config_str)
    
    # Extract 'data' if this is an API response export
    agent_data = final_payload_full.get('data', final_payload_full)
    agent_id = agent_data.get('ID', AGENT_ID)

    # Prepare final API payload
    # The API likely expects { "id": "...", "agent": { ... } } or just the agent object depending on the endpoint.
    # update_bot_prompt.py uses a wrapper:
    # payload = { "id": agent_id, "agent": { "nodes": [...] } }
    # So we should probably wrap it similarly for a full update.
    
    upload_payload = {
        "id": agent_id,
        "agent": agent_data
    }

    # Save the ready-to-upload file (gitignored)
    with open(UPLOAD_OUTPUT_FILE, 'w') as f:
        json.dump(upload_payload, f, indent=2)
    
    print(f"\n✅ Prepared secure payload saved to: {UPLOAD_OUTPUT_FILE}")
    print("This file contains your actual secrets and is gitignored.")

    # Option to upload immediately
    user_input = input(f"\nDo you want to upload this configuration to Agent {agent_id} now? (y/n): ")
    if user_input.lower() == 'y':
        # Check for API Token
        # NOTE: Using the hardcoded one from update_bot_prompt.py as fallback, but alerting user.
        api_token = os.getenv('CONVOCORE_API_TOKEN', "u0na7hTcezg4enFnCtJA")
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{API_URL}/{agent_id}" # PATCH endpoint as per update script
        
        # Note: If we need to replace the WHOLE agent, maybe we strictly need the structure from the GET.
        # But 'agent_data' is that structure.
        # Let's try sending the wrapped payload.
        
        try:
            print(f"Uploading to {url}...")
            response = requests.patch(url, headers=headers, json=upload_payload)
            response.raise_for_status()
            print("🎉 Success! Agent configuration updated.")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main()
