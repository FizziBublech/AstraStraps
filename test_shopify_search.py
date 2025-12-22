import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_search():
    domain = os.environ.get('SHOPIFY_STORE_DOMAIN')
    token = os.environ.get('SHOPIFY_ADMIN_TOKEN')
    version = os.environ.get('SHOPIFY_API_VERSION', '2024-10')
    url = f"https://{domain}/admin/api/{version}/graphql.json"
    
    headers = {
        'X-Shopify-Access-Token': token,
        'Content-Type': 'application/json'
    }
    
    query = """
    query($q: String!) {
      orders(first: 1, query: $q) {
        edges { node { id name processedAt cancelledAt closedAt displayFinancialStatus displayFulfillmentStatus
          customer { displayName email }
          shippingAddress { name address1 address2 city province country zip phone }
          fulfillments { createdAt status trackingInfo { number url company } }
          lineItems(first: 50) { edges { node { name quantity sku variant { id title image { url } product { id title handle onlineStoreUrl } } } } }
        } }
      }
    }
    """
    
    for name in ["#141808", "141808"]:
        q = f'name:"{name}"'
        response = requests.post(url, headers=headers, json={"query": query, "variables": {"q": q}})
        print(f"Query for {q}: status {response.status_code}")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_search()
