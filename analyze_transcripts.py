import os
import json
import requests
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

AGENT_ID = os.environ.get("CONVOCORE_AGENT_ID", "QTbeXwvOediCAv2")
CONVOCORE_API_KEY = os.environ.get("CONVOCORE_API_KEY", "u0na7hTcezg4enFnCtJA")
# User mentioned both na and eu, but export worked on na
BASE_URL = os.environ.get("CONVOCORE_BASE_URL", "https://na-gcp-api.vg-stuff.com/v3")

def fetch_conversations():
    """Download latest conversations via export API."""
    print("Fetching conversations from Convocore...")
    url = f"{BASE_URL}/agents/{AGENT_ID}/convos/export?format=json"
    headers = {"Authorization": f"Bearer {CONVOCORE_API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

def format_transcript(convo):
    """Convert JSON conversation structure to readable text."""
    transcript = []
    # Some metadata
    meta = convo.get('metadata', {}).get('convo', {})
    convo_id = meta.get('id', 'Unknown')
    
    for turn in convo.get('turns', []):
        role = turn.get('from', 'unknown')
        for msg in turn.get('messages', []):
            m_type = msg.get('type')
            payload = msg.get('payload', {})
            
            if m_type == 'text':
                text = payload.get('message', '')
                if text:
                    transcript.append(f"{role.upper()}: {text}")
            elif m_type == 'choice':
                options = [b.get('name') for b in payload.get('buttons', [])]
                transcript.append(f"BOT (CHOICE): {', '.join(options)}")
            elif m_type == 'debug:tell':
                # Skip debug info unless it's useful
                pass
            
    return "\n".join(transcript)

def analyze_with_gemini(transcript):
    """Analyze transcript using Gemini API."""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-flash-lite-latest"
    prompt = f"""
Analyze the following customer service chatbot transcript.
Return your analysis in the following format:
TECHNICAL_ERROR: [YES/NO] - Briefly explain if any.
UNHAPPY_CUSTOMER: [YES/NO] - Briefly explain if any.
SUMMARY: [A concise summary of the interaction and any unresolved issues]

Transcript:
\"\"\"
{transcript}
\"\"\"
"""
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
    )

    full_response = ""
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response += chunk.text
    except Exception as e:
        return f"Gemini Error: {e}"
        
    return full_response.strip()

import argparse

def main():
    parser = argparse.ArgumentParser(description="Analyze Convocore transcripts with Gemini.")
    parser.add_argument("--date", help="Date to analyze (YYYY-MM-DD).")
    parser.add_argument("--month", help="Month to analyze (YYYY-MM).")
    parser.add_argument("--limit", type=int, help="Limit number of conversations to analyze.", default=20)
    args = parser.parse_args()

    data = fetch_conversations()
    if not data or 'data' not in data:
        print("No conversation data found.")
        return

    target_date = args.date
    target_month = args.month
    
    if not target_date and not target_month:
        target_date = datetime.now().strftime("%Y-%m-%d")
        print(f"No date or month specified. Defaulting to today: {target_date}")

    convos = data['data']
    
    # Filter by date or month
    filtered_convos = []
    for convo in convos:
        ts = convo['metadata']['convo'].get('ts', 0)
        dt_obj = datetime.fromtimestamp(ts)
        convo_date = dt_obj.strftime('%Y-%m-%d')
        convo_month = dt_obj.strftime('%Y-%m')
        
        if target_date and convo_date == target_date:
            filtered_convos.append(convo)
        elif target_month and convo_month == target_month:
            filtered_convos.append(convo)

    if not filtered_convos:
        msg = f"date {target_date}" if target_date else f"month {target_month}"
        print(f"No conversations found for {msg}.")
        return

    filtered_convos.sort(key=lambda x: x['metadata']['convo'].get('ts', 0), reverse=True)
    
    # Apply limit
    final_convos = filtered_convos[:args.limit]
    
    print(f"Analyzing {len(final_convos)} conversations from {target_date or target_month}...\n")
    
    results = []
    error_count = 0
    dissatisfied_count = 0

    for convo in final_convos:
        convo_id = convo['metadata']['convo']['id']
        ts = convo['metadata']['convo']['ts']
        dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        
        transcript_text = format_transcript(convo)
        if not transcript_text:
            continue
            
        print(f"ID: {convo_id} | Date: {dt}")
        analysis = analyze_with_gemini(transcript_text)
        print(f"Analysis:\n{analysis}\n")
        print("-" * 50)
        
        is_error = "TECHNICAL_ERROR: YES" in analysis.upper().replace('[', '').replace(']', '')
        is_unhappy = "UNHAPPY_CUSTOMER: YES" in analysis.upper().replace('[', '').replace(']', '')
        
        if is_error: error_count += 1
        if is_unhappy: dissatisfied_count += 1
        
        results.append({
            "id": convo_id,
            "date": dt,
            "is_technical_error": is_error,
            "is_unhappy_customer": is_unhappy,
            "analysis": analysis
        })

    print(f"\n--- Final Report Summary ---")
    print(f"Date/Month Analyzed: {target_date or target_month}")
    print(f"Total Conversations Analyzed: {len(results)}")
    print(f"Technical Errors Found: {error_count}")
    print(f"Unhappy Customers Found: {dissatisfied_count}")

    label = target_date or target_month
    report_file = f"analysis_report_{label}_{datetime.now().strftime('%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Full report saved to {report_file}")

if __name__ == "__main__":
    main()
