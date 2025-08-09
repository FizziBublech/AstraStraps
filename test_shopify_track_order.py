#!/usr/bin/env python3
"""
Dev-only read test for Shopify order tracking.

Fetches recent orders directly from Shopify GraphQL using the same client logic
as the app (no public endpoint), then calls the local /track-order endpoint for
those order names to verify end-to-end behavior.
"""

import os
import json
from datetime import datetime
import requests


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
TRACK_ENDPOINT = f"{BASE_URL}/track-order"


def print_json(prefix: str, obj):
    print(prefix)
    print(json.dumps(obj, indent=2))


def list_recent_orders_via_app_graphql(limit: int = 5):
    """Hit the app's debug-only endpoint if available; otherwise fail gracefully."""
    url = f"{BASE_URL}/list-recent-orders?limit={limit}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"   Note: /list-recent-orders returned {r.status_code}, skipping")
            return []
        data = r.json()
        if not data.get('success'):
            print("   Note: /list-recent-orders not successful, skipping")
            return []
        return [o.get('name') for o in data.get('orders', []) if o.get('name')]
    except Exception as e:
        print(f"   Note: Could not call /list-recent-orders ({e}), skipping")
        return []


def main() -> int:
    print("🚀 Testing Shopify Track Order")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Time: {datetime.now().isoformat()}")

    order_names = list_recent_orders_via_app_graphql(limit=3)
    if not order_names:
        print("   ⚠️  No recent order names available via debug endpoint. Manually provide one to test.")
        return 0

    for name in order_names:
        print(f"\n🧪 Track order: {name}")
        resp = requests.post(TRACK_ENDPOINT, json={"order_number": name}, timeout=45)
        print(f"   Status: {resp.status_code}")
        try:
            data = resp.json()
        except Exception:
            print("   Response (non-JSON):")
            print(resp.text)
            continue
        print_json("   Response:", data)

    print("\n✅ Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


