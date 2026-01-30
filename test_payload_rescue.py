import logging
import json
from main import extract_payload, app

# Configure logging to see the "Rescue" messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction():
    print("--- Starting Extraction Tests ---")

    test_cases = [
        {
            "name": "Standard Clean JSON",
            "input": {
                "customer_email": "test@example.com",
                "issue": "My watch band broke",
                "order_number": "#1001"
            },
            "expected_issue": "My watch band broke"
        },
        {
            "name": "Stuffed JSON (Double Quotes)",
            "input": {
                "customer_email": "test@example.com",
                "issue": "My issue is bad\", \"order_number\": \"#1002"
            },
            "expected_issue": "My issue is bad",
            "expected_order": "#1002"
        },
        {
            "name": "Stuffed JSON (Single Quotes)",
            "input": {
                "customer_email": "test@example.com",
                "issue": "My issue is bad', 'order_number': '#1003"
            },
            "expected_issue": "My issue is bad",
            "expected_order": "#1003"
        },
        {
            "name": "UI Fragment Contamination",
            "input": {
                "customer_email": "test@example.com",
                "issue": [{"type": "text", "text": "I need help with a return"}]
            },
            "expected_issue": "I need help with a return"
        },
        {
            "name": "Complex Stuffed with UI Fragment (Hard Mode)",
            "input": {
                 "order_number": "#9999\", \"issue\": \"[{\"type\": \"text\", \"text\": \"Help me\"}]"
            },
            "expected_order": "#9999",
            # Note: The current aggressive regex might just extract the string representation.
            # Ideally we want it to handle this, but let's see what it does.
        }
    ]

    passed = 0
    failed = 0

    with app.test_request_context():
        for i, case in enumerate(test_cases):
            print(f"\nTest Case {i+1}: {case['name']}")
            print(f"Input: {json.dumps(case['input'], indent=2)}")
            
            result = extract_payload(case['input'])
            print(f"Result: {json.dumps(result, indent=2)}")

            # Validation
            success = True
            
            if "expected_issue" in case:
                if result.get("issue") != case["expected_issue"]:
                    print(f"❌ FAIL: Expected issue '{case['expected_issue']}', got '{result.get('issue')}'")
                    success = False
            
            if "expected_order" in case:
                if result.get("order_number") != case["expected_order"]:
                    print(f"❌ FAIL: Expected order '{case['expected_order']}', got '{result.get('order_number')}'")
                    success = False

            if success:
                print("✅ PASS")
                passed += 1
            else:
                failed += 1

    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    test_extraction()
