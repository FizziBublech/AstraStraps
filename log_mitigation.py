import argparse
import json
import os
from datetime import datetime

TRACKER_FILE = "issue_tracker.json"

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_tracker(data):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Log mitigation notes for an issue.")
    parser.add_argument("--id", required=True, help="The ID of the conversation/issue.")
    parser.add_argument("--note", required=True, help="The mitigation note to add.")
    parser.add_argument("--status", help="Update status (e.g., Resolved, Investigating).", default=None)
    
    args = parser.parse_args()
    
    tracker = load_tracker()
    found = False
    
    for issue in tracker:
        if issue['id'] == args.id:
            found = True
            current_notes = issue.get('mitigation_notes', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_note = f"[{timestamp}] {args.note}"
            
            if current_notes:
                issue['mitigation_notes'] = current_notes + "\n" + new_note
            else:
                issue['mitigation_notes'] = new_note
                
            if args.status:
                issue['status'] = args.status
                print(f"Updated status to: {args.status}")
                
            print(f"Added mitigation note to issue {args.id}")
            break
            
    if found:
        save_tracker(tracker)
    else:
        print(f"Issue with ID {args.id} not found.")

if __name__ == "__main__":
    main()
