#!/usr/bin/env python3
"""
Read-only tests for the Shopify product recommendation endpoint.

This script exercises /recommend-products with a variety of queries and
structured filters and prints the responses for quick inspection.
"""

import os
import json
from datetime import datetime
import requests


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
ENDPOINT = f"{BASE_URL}/recommend-products"


def print_response(label: str, response: requests.Response) -> None:
    print(f"\n🧪 {label}")
    print(f"   POST {ENDPOINT}")
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        print("   Response:")
        print(json.dumps(data, indent=2))
    except Exception:
        print("   Response (non-JSON):")
        print(response.text)


def post_payload(payload: dict) -> requests.Response:
    return requests.post(ENDPOINT, json=payload, timeout=45)


def main() -> int:
    print("🚀 Testing Shopify Product Recommendations")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Time: {datetime.now().isoformat()}")

    tests = [
        (
            "Generic query: 'strap' (limit 2)",
            {"query_text": "strap", "limit": 2},
        ),
        (
            "Apple Watch strap with filters (Series 7, 45mm, leather, black)",
            {
                "query_text": "apple watch strap",
                "filters": {
                    "watch_model": "Series 7",
                    "size": "45mm",
                    "material": "leather",
                    "color": "black",
                },
                "limit": 3,
            },
        ),
        (
            "Material-only filter (leather)",
            {
                "filters": {
                    "material": "leather"
                },
                "limit": 3,
            },
        ),
        (
            "Free-text: 'nylon strap 41mm'",
            {"query_text": "nylon strap 41mm", "limit": 3},
        ),
        (
            "Likely no results: 'zzzz-nonexistent-product'",
            {"query_text": "zzzz-nonexistent-product", "limit": 3},
        ),
        (
            "Budget filter under $25 (any material)",
            {
                "filters": {
                    "price_max": 25
                },
                "limit": 5,
            },
        ),
        (
            "Color filter: blue or pink (any strap)",
            {
                "filters": {
                    "colors": ["blue", "pink"]
                },
                "limit": 5,
            },
        ),
        (
            "On sale only (compare_at_price > price)",
            {
                "filters": {
                    "on_sale": True
                },
                "limit": 5,
            },
        ),
        (
            "Watch model + size + budget (Series 7, 41mm, <= $30)",
            {
                "filters": {
                    "watch_model": "Series 7",
                    "size": "41mm",
                    "price_max": 30
                },
                "limit": 5,
            },
        ),
        (
            "Leather under $40 in brown or black",
            {
                "filters": {
                    "material": "leather",
                    "colors": ["brown", "black"],
                    "price_max": 40
                },
                "limit": 5,
            },
        ),
    ]

    for label, payload in tests:
        try:
            resp = post_payload(payload)
            print_response(label, resp)
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error for '{label}': {e}")

    print("\n✅ Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


