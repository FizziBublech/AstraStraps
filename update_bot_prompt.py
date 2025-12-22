import os
import json
import shutil
import argparse
import requests
from datetime import datetime

# Configuration
AGENT_ID = "QTbeXwvOediCAv2"
API_TOKEN = "u0na7hTcezg4enFnCtJA" # In a real app, load from os.environ
BASE_URL = "https://na-gcp-api.vg-stuff.com/v3/agents"
PROMPTS_DIR = "prompts"
ARCHIVE_DIR = os.path.join(PROMPTS_DIR, "archive")
HISTORY_FILE = os.path.join(PROMPTS_DIR, "history.json")
CURRENT_PROMPT_FILE = os.path.join(PROMPTS_DIR, "current.md")

def get_headers():
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

def fetch_agent_config(agent_id):
    """Fetches the current agent configuration from the API."""
    url = f"{BASE_URL}/{agent_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def get_current_instructions(agent_data):
    """Extracts the instructions from the agent data."""
    # Based on the user's curl example and typical structure
    if 'data' in agent_data:
        data = agent_data['data']
        if 'nodes' in data:
            for node in data['nodes']:
                if node.get('id') == '__start__':
                    return node.get('instructions')
    return None

def archive_prompt(content, version_label):
    """Archives the prompt content to a file."""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    
    filename = f"prompt_{version_label}.md"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def update_history(version_label, author, message, filepath):
    """Updates the history.json manifest."""
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "version": version_label,
        "author": author,
        "message": message,
        "file": filepath
    }
    
    history.insert(0, entry) # Prepend new entry
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

def update_agent(agent_id, new_instructions, dry_run=False):
    """Updates the agent with the new instructions."""
    
    # Construct the payload
    # We are only updating the instructions of the start node
    # The structure must match what the API expects for a PATCH
    
    # First, we need to get the current object to ensure we don't overwrite other things
    # OR we can send a partial update if the API supports it. 
    # The user's example suggests sending:
    # { "id": "...", "agent": { "nodes": [...] } }
    # Let's try to mimic that structure but we might need to be careful about not deleting other nodes.
    # Safest is to fetch, update local object, then send back (or send just the specific node if API allows).
    # Given the user's example:
    # {
    #   "id": "your_agent_id",
    #   "agent": {
    #     "nodes": [
    #       {
    #         "id": "__start__",
    #         "instructions": "..."
    #       }
    #     ]
    #   }
    # }
    # This implies a specific update format. Let's assume this "merge" behavior works as documented by user.
    
    payload = {
        "id": agent_id,
        "agent": {
            "nodes": [
                {
                    "id": "__start__",
                    "instructions": new_instructions
                }
            ]
        }
    }

    if dry_run:
        print(f"[DRY RUN] Would PATCH to {BASE_URL}/{agent_id}")
        # print(json.dumps(payload, indent=2))
        return True

    url = f"{BASE_URL}/{agent_id}"
    response = requests.patch(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return True

def main():
    parser = argparse.ArgumentParser(description="Update AstraBot prompt with versioning.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the update without making API calls.")
    parser.add_argument("--message", "-m", type=str, default="Automated update", help="Commit message for this version.")
    parser.add_argument("--author", "-a", type=str, default="script", help="Author of the change.")
    parser.add_argument("--agent-id", type=str, default=AGENT_ID, help=f"Agent ID to update (default: {AGENT_ID})")
    
    args = parser.parse_args()
    
    target_agent_id = args.agent_id
    
    print(f"--- AstraBot Prompt Updater ---")
    print(f"Target Agent ID: {target_agent_id}")
    
    # 1. Read new prompt
    try:
        with open(CURRENT_PROMPT_FILE, 'r', encoding='utf-8') as f:
            new_prompt_content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {CURRENT_PROMPT_FILE}")
        return

    # 2. Fetch current config (to archive it)
    print("Fetching current agent configuration...")
    try:
        current_config = fetch_agent_config(target_agent_id)
        old_instructions = get_current_instructions(current_config)
    except Exception as e:
        print(f"Error fetching agent config: {e}")
        return

    # 3. Archive old Instructions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if old_instructions:
        print("Archiving current (old) instructions...")
        if args.dry_run:
             print(f"[DRY RUN] Would archive old prompt to prompts/archive/prompt_old_{timestamp}.md")
        else:
            archive_prompt(old_instructions, f"old_{timestamp}")
    else:
        print("Warning: No existing instructions found to archive.")

    # 4. Archive NEW Instructions (as the 'deployed' version)
    version_label = f"v_{timestamp}"
    print(f"Preparing version {version_label}...")
    
    if args.dry_run:
        print(f"[DRY RUN] Would copy {CURRENT_PROMPT_FILE} to {ARCHIVE_DIR}/prompt_{version_label}.md")
        print(f"[DRY RUN] Would update history.json with message: '{args.message}'")
    else:
        saved_path = archive_prompt(new_prompt_content, version_label)
        update_history(version_label, args.author, args.message, saved_path)

    # 5. Push update
    print("Updating agent...")
    try:
        update_agent(target_agent_id, new_prompt_content, dry_run=args.dry_run)
        print("Success! Agent prompt updated.")
    except Exception as e:
        print(f"Failed to update agent: {e}")

if __name__ == "__main__":
    main()
