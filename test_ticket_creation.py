#!/usr/bin/env python3
"""
Test script for ticket creation endpoint

⚠️  WARNING: This will create a REAL support ticket in your Reamaze account!
Only run this if you want to test the ticket creation functionality.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_ticket_creation():
    """Test creating a support ticket"""
    
    print("⚠️  WARNING: This will create a REAL support ticket!")
    print("   This ticket will appear in your Reamaze inbox.")
    print("   Only proceed if you want to test this functionality.")
    
    response = input("\nDo you want to proceed? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Ticket creation test cancelled.")
        return
    
    print("\n🎫 Testing Ticket Creation...")
    
    # Test data
    ticket_data = {
        "customer_email": "alex@droidcorp.ai",
        "customer_name": "Test Customer",
        "issue_summary": "Flask API Bridge Test Ticket",
        "order_number": "TEST-12345"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/create-ticket",
            json=ticket_data,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print("   ✅ Ticket created successfully!")
            print(f"   📧 Check your Reamaze inbox for ticket ID: {result.get('ticket_id')}")
        else:
            print("   ❌ Ticket creation failed")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_ticket_creation() 