import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")
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

def delete_convo(convo_id):
    """Delete a conversation from Convocore."""
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/{convo_id}"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error deleting convo {convo_id}: {e}")
        return False

def process_report(report_path, dry_run=False):
    if not os.path.exists(report_path):
        print(f"Report not found: {report_path}")
        return

    with open(report_path, 'r') as f:
        results = json.load(f)

    tracker = load_tracker()
    existing_ids = {issue['id'] for issue in tracker}
    
    new_issues_added = 0
    deletions_attempted = 0
    deletions_successful = 0

    for item in results:
        if item.get('is_technical_error') or item.get('is_unhappy_customer'):
            convo_id = item['id']
            
            # Find existing issue or create new one
            existing_issue = next((issue for issue in tracker if issue['id'] == convo_id), None)
            
            if existing_issue:
                # If it's a technical error and wasn't deleted, try to delete it now (if not dry run)
                should_delete = existing_issue.get("is_technical_error")
                if should_delete and not existing_issue.get("deleted_from_frontend") and not dry_run:
                    print(f"Retrying deletion for technical error in convo: {convo_id}")
                    if delete_convo(convo_id):
                        existing_issue["deleted_from_frontend"] = True
                        deletions_successful += 1
                        new_issues_added += 1 # Trigger save
                    deletions_attempted += 1
            else:
                # New issue
                is_tech_error = item.get('is_technical_error', False)
                new_issue = {
                    "id": convo_id,
                    "date": item['date'],
                    "is_technical_error": is_tech_error,
                    "is_unhappy_customer": item.get('is_unhappy_customer', False),
                    "analysis": item['analysis'],
                    "status": "Pending",
                    "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "deleted_from_frontend": False
                }
                
                print(f"Logging new issue in convo: {convo_id}")
                
                if not dry_run:
                    if is_tech_error:
                        print(f"Deleting technical error: {convo_id}")
                        if delete_convo(convo_id):
                            new_issue["deleted_from_frontend"] = True
                            deletions_successful += 1
                        deletions_attempted += 1
                    tracker.append(new_issue)
                    new_issues_added += 1
                else:
                    action = "log and delete" if is_tech_error else "log"
                    print(f"[DRY RUN] Would {action} convo: {convo_id}")

    if new_issues_added > 0:
        save_tracker(tracker)
        print(f"\nSuccess: Added {new_issues_added} new issues to the tracker.")
        if not dry_run:
            print(f"Deletions: {deletions_successful}/{deletions_attempted} successful.")
    else:
        print("No new issues found in the report.")

def main():
    parser = argparse.ArgumentParser(description="Process analysis reports and manage issues.")
    parser.add_argument("report", help="Path to the JSON analysis report.")
    parser.add_argument("--dry-run", action="store_true", help="Log issues without deleting from API.")
    args = parser.parse_args()

    process_report(args.report, args.dry_run)

if __name__ == "__main__":
    main()
