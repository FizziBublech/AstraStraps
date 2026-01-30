import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TRACKER_FILE = "issue_tracker.json"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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

def classify_issue(analysis_text):
    """Ask Gemini to classify the issue based on its existing analysis."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    model = "gemini-flash-lite-latest"
    prompt = f"""
    Analyze the following issue summary and classify the error.
    
    Return the result in this exact format:
    CATEGORY: [One of: SYSTEM, LOGIC, DATA, UI, NLU, PRODUCT_DATABASE, LLM_NETWORK, OTHER]
    TAG: [A short, specific 2-4 word tag describing the specific error, e.g., "Database Timeout", "Looping", "Validation Failed"]
    
    If there is no technical error mentioned, return:
    CATEGORY: NONE
    TAG: NONE
    
    Analysis Text:
    \"\"\"
    {analysis_text}
    \"\"\"
    """
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def parse_classification(response_text):
    category = "NONE"
    tag = "NONE"
    
    if not response_text:
        return category, tag
        
    for line in response_text.split('\n'):
        if "CATEGORY:" in line:
            category = line.split(":", 1)[1].strip().upper()
        if "TAG:" in line:
            tag = line.split(":", 1)[1].strip()
            
    return category, tag

def main():
    tracker = load_tracker()
    updated_count = 0
    
    print(f"Found {len(tracker)} issues. Starting backfill...")
    
    for issue in tracker:
        # Check if we need to backfill (missing category or it's the old generic 'NONE' without a tag)
        needs_update = "error_category" not in issue or "error_tag" not in issue
        
        # Also re-process if it has is_technical_error=True but category is NONE/missing
        if issue.get("is_technical_error") and (issue.get("error_category", "NONE") == "NONE"):
            needs_update = True
            
        if needs_update and issue.get("analysis"):
            print(f"Processing issue {issue['id']}...")
            
            response = classify_issue(issue['analysis'])
            if response:
                category, tag = parse_classification(response)
                issue['error_category'] = category
                issue['error_tag'] = tag
                updated_count += 1
                print(f"  -> Classified as {category} | {tag}")
            
            # Rate limiting check (simple)
            time.sleep(1) 
            
    if updated_count > 0:
        save_tracker(tracker)
        print(f"\nSuccessfully updated {updated_count} issues.")
    else:
        print("\nNo issues needed updating.")

if __name__ == "__main__":
    main()
