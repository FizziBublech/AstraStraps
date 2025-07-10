#!/usr/bin/env python3
"""
Test script for the Reamaze API Bridge

This script tests the API endpoints safely without creating support tickets.
Only read-only endpoints (search-kb, get-instructions) are tested with the live API.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None, description=""):
    """Test an API endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🧪 Testing: {description}")
    print(f"   {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Reamaze API Bridge Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Time: {datetime.now().isoformat()}")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health Check
    total_tests += 1
    if test_endpoint("/", "GET", description="Health Check"):
        tests_passed += 1
    
    # Test 2: Search Knowledge Base - Valid Query
    total_tests += 1
    search_data = {
        "query_term": "apple watch",
        "max_results": 3
    }
    if test_endpoint("/search-kb", "POST", search_data, "Search KB - Valid Query"):
        tests_passed += 1
    
    # Test 3: Search Knowledge Base - Missing Query
    total_tests += 1
    invalid_search = {}
    if test_endpoint("/search-kb", "POST", invalid_search, "Search KB - Missing Query (should fail)"):
        # This should fail, so we don't increment passed
        pass
    else:
        tests_passed += 1  # Expected failure
    
    # Test 4: Get Instructions - By Topic
    total_tests += 1
    instructions_data = {
        "topic": "leather strap"
    }
    if test_endpoint("/get-instructions", "POST", instructions_data, "Get Instructions - By Topic"):
        tests_passed += 1
    
    # Test 5: Get Instructions - Missing Parameters
    total_tests += 1
    invalid_instructions = {}
    if test_endpoint("/get-instructions", "POST", invalid_instructions, "Get Instructions - Missing Params (should fail)"):
        # This should fail, so we don't increment passed
        pass
    else:
        tests_passed += 1  # Expected failure
    
    # Test 6: Invalid Endpoint
    total_tests += 1
    if test_endpoint("/invalid-endpoint", "GET", description="Invalid Endpoint (should return 404)"):
        # This should fail, so we don't increment passed
        pass
    else:
        tests_passed += 1  # Expected failure
    
    # Print Summary
    print(f"\n📊 Test Results")
    print(f"   Passed: {tests_passed}/{total_tests}")
    print(f"   Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("   ✅ All tests passed!")
        return 0
    else:
        print("   ❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1) 