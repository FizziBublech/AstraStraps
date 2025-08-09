import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    Config.validate_config()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Human-readable mappings for Reamaze codes
STATUS_CODES = {
    0: "Unresolved",
    1: "Pending",
    2: "Resolved", 
    3: "Spam",
    4: "Archived",
    5: "On Hold",
    6: "Auto-Resolved",
    7: "Chatbot Assigned",
    8: "Chatbot Resolved",
    9: "Spam - identified by AI"
}

ORIGIN_CODES = {
    0: "Chat",
    1: "Email",
    2: "Twitter",
    3: "Facebook",
    6: "Classic Mode Chat",
    7: "API",
    8: "Instagram",
    9: "SMS",
    15: "WhatsApp",
    16: "Staff Outbound",
    17: "Contact Form"
}

CHANNEL_CODES = {
    1: "Email",
    2: "Twitter", 
    3: "Facebook",
    6: "Chat",
    7: "API",
    8: "Instagram",
    9: "SMS"
}

class ReamazeAPIClient:
    """Client for interacting with the Reamaze API"""
    
    def __init__(self):
        self.base_url = app.config['REAMAZE_BASE_URL']
        self.auth = HTTPBasicAuth(app.config['REAMAZE_EMAIL'], app.config['REAMAZE_API_TOKEN'])
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to Reamaze API with error handling and retries"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(app.config['RATE_LIMIT_RETRIES']):
            try:
                logger.info(f"Making {method} request to {url}")
                
                response = requests.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=30
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 429:  # Rate limited
                    if attempt < app.config['RATE_LIMIT_RETRIES'] - 1:
                        logger.warning(f"Rate limited, retrying in {app.config['RATE_LIMIT_DELAY']} seconds")
                        time.sleep(app.config['RATE_LIMIT_DELAY'])
                        continue
                    else:
                        return {"error": "Rate limit exceeded", "status_code": 429}
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < app.config['RATE_LIMIT_RETRIES'] - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {"error": str(e), "status_code": 500}
        
        return {"error": "Max retries exceeded", "status_code": 500}
    
    def create_conversation(self, subject, body, customer_email, customer_name=None):
        """Create a new conversation (support ticket)"""
        data = {
            "conversation": {
                "subject": subject,
                "category": "astra-straps",  # Use the correct channel slug
                "user": {
                    "email": customer_email,
                    "name": customer_name or customer_email
                },
                "message": {
                    "body": body
                }
            }
        }
        
        return self._make_request('POST', '/conversations', data=data)
    
    def search_articles(self, query, limit=5):
        """Search knowledge base articles"""
        params = {
            'q': query,
            'limit': limit
        }
        
        return self._make_request('GET', '/articles', params=params)
    
    def get_article(self, article_id):
        """Get a specific article by ID"""
        return self._make_request('GET', f'/articles/{article_id}')
    
    def get_conversations(self, for_email=None, q=None, limit=10, page=1):
        """Retrieve conversations with optional filtering"""
        params = {
            'limit': limit,
            'page': page
        }
        
        # Add email filter if provided
        if for_email:
            params['for'] = for_email
            
        # Add search query if provided (for order numbers, etc.)
        if q:
            params['q'] = q
            
        return self._make_request('GET', '/conversations', params=params)
    
    def get_conversation(self, conversation_id):
        """Get a specific conversation by ID"""
        return self._make_request('GET', f'/conversations/{conversation_id}')
    
    def add_message_to_conversation(self, conversation_id, body, author_email, author_name=None):
        """Add a new message to an existing conversation"""
        data = {
            "message": {
                "body": body,
                "user": {
                    "email": author_email,
                    "name": author_name or author_email
                }
            }
        }
        
        return self._make_request('POST', f'/conversations/{conversation_id}/messages', data=data)

# Initialize API client
reamaze_client = ReamazeAPIClient()

class ShopifyAPIClient:
    """Client for interacting with the Shopify Admin API (REST + GraphQL)"""

    def __init__(self):
        self.store_domain = app.config.get('SHOPIFY_STORE_DOMAIN')
        self.admin_token = app.config.get('SHOPIFY_ADMIN_TOKEN')
        self.api_version = app.config.get('SHOPIFY_API_VERSION')
        self.rest_base_url = app.config.get('SHOPIFY_ADMIN_REST_BASE_URL')
        self.graphql_url = app.config.get('SHOPIFY_ADMIN_GRAPHQL_URL')

        if not self.store_domain or not self.admin_token:
            logger.warning("Shopify configuration not set. Shopify endpoints will not function until configured.")

        self.rest_headers = {
            'X-Shopify-Access-Token': self.admin_token or '',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _graphql(self, query: str, variables: dict):
        if not self.graphql_url:
            return {"error": "Shopify not configured", "status_code": 500}
        try:
            response = requests.post(
                self.graphql_url,
                headers={
                    'X-Shopify-Access-Token': self.admin_token,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                json={"query": query, "variables": variables},
                timeout=30
            )
            logger.info(f"Shopify GraphQL status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            if 'errors' in data and data['errors']:
                return {"error": str(data['errors']), "status_code": 400}
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Shopify GraphQL request failed: {e}")
            return {"error": str(e), "status_code": 500}

    def get_order_by_number(self, order_number: str):
        """Find a single order by name (e.g., #1001), using GraphQL search and a wider recent scan."""
        # 1) Try GraphQL search by name (with and without #)
        potential_names = [f"#{str(order_number).strip()}", str(order_number).strip()]
        search_gql = """
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
        for name in potential_names:
            q = f'name:"{name}"'
            data = self._graphql(search_gql, {"q": q})
            if isinstance(data, dict):
                edges = (((data or {}).get('orders') or {}).get('edges'))
                if edges:
                    return edges[0].get('node')

        # 2) Scan a wider recent window (up to 250 most recent) and match by name
        scan_gql = """
        query($first: Int!) {
          orders(first: $first, sortKey: PROCESSED_AT, reverse: true) {
            edges { node { id name processedAt cancelledAt closedAt displayFinancialStatus displayFulfillmentStatus
              customer { displayName email }
              shippingAddress { name address1 address2 city province country zip phone }
              fulfillments { createdAt status trackingInfo { number url company } }
              lineItems(first: 50) { edges { node { name quantity sku variant { id title image { url } product { id title handle onlineStoreUrl } } } } }
            } }
          }
        }
        """
        data = self._graphql(scan_gql, {"first": 250})
        if not isinstance(data, dict):
            return None
        edges = (((data or {}).get('orders') or {}).get('edges'))
        if not edges:
            return None
        targets = set(potential_names)
        for edge in edges:
            node = edge.get('node', {})
            if node.get('name') in targets:
                return node
        return None

    def search_products(self, query_text: str = None, filters: dict = None, limit: int = 5):
        """Search products via GraphQL using Shopify's search syntax"""
        tokens = []
        filters = filters or {}
        if query_text:
            tokens.append(query_text)
        # Common structured filters mapped to tags/title/vendor/type
        if filters.get('product_type'):
            tokens.append(f"product_type:{filters['product_type']}")
        if filters.get('vendor'):
            tokens.append(f"vendor:{filters['vendor']}")
        if filters.get('tag'):
            tokens.append(f"tag:\"{filters['tag']}\"")
        # Map watch related hints into generic tokens (tags/title contains)
        for key in ['watch_model', 'size', 'material', 'color']:
            if filters.get(key):
                value = str(filters[key]).strip()
                if value:
                    tokens.append(f"title:{value}")
                    tokens.append(f"tag:\"{value}\"")

        q = " ".join(tokens) if tokens else None
        if not q:
            # Fallback to return recently updated products
            q = "status:active"

        gql = """
        query($q: String!, $first: Int!) {
          products(first: $first, query: $q) {
            edges {
              node {
                id
                title
                handle
                onlineStoreUrl
                featuredImage { url }
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      sku
                      price
                      compareAtPrice
                      image { url }
                    }
                  }
                }
              }
            }
          }
        }
        """

        data = self._graphql(gql, {"q": q, "first": max(1, min(limit, 25))})
        if "error" in data:
            return data

        edges = (((data or {}).get('products') or {}).get('edges')) if isinstance(data, dict) else None
        products = []
        if edges:
            for edge in edges:
                node = edge.get('node', {})
                handle = node.get('handle')
                online_url = node.get('onlineStoreUrl') or (f"https://{self.store_domain}/products/{handle}" if self.store_domain and handle else None)
                image = (node.get('featuredImage') or {}).get('url')
                # Build variants
                variants = []
                for v_edge in (node.get('variants', {}).get('edges') or []):
                    v = v_edge.get('node', {})
                    # Extract numeric variant id for storefront URLs
                    variant_gid = v.get('id') or ''
                    variant_numeric_id = None
                    if isinstance(variant_gid, str) and '/' in variant_gid:
                        variant_numeric_id = variant_gid.split('/')[-1]
                    # Variant-specific URL if possible
                    variant_url = None
                    if online_url and variant_numeric_id:
                        separator = '&' if '?' in (online_url or '') else '?'
                        variant_url = f"{online_url}{separator}variant={variant_numeric_id}"

                    # Variant image fallback to product image
                    variant_image = ((v.get('image') or {}).get('url')) or image
                    variants.append({
                        "id": v.get('id'),
                        "title": v.get('title'),
                        "sku": v.get('sku'),
                        "price": v.get('price'),
                        "compare_at_price": v.get('compareAtPrice'),
                        "currency": None,
                        "image": variant_image,
                        "url": variant_url
                    })
                
                # Post-filtering by price/colors/size/sale if provided
                def to_float_or_none(value):
                    if value is None:
                        return None
                    if isinstance(value, (int, float)):
                        return float(value)
                    try:
                        s = str(value).strip()
                        if not s:
                            return None
                        return float(s)
                    except Exception:
                        return None

                price_min_val = to_float_or_none(filters.get('price_min'))
                price_max_val = to_float_or_none(filters.get('price_max'))

                on_sale_raw = filters.get('on_sale')
                if isinstance(on_sale_raw, str):
                    on_sale = on_sale_raw.strip().lower() in ("1", "true", "yes", "y")
                else:
                    on_sale = bool(on_sale_raw)
                # Accept 'color' or 'colors'
                colors_filter = filters.get('colors') or filters.get('color')
                if isinstance(colors_filter, str):
                    colors = [colors_filter]
                else:
                    colors = colors_filter or []
                colors = [str(c).strip().lower() for c in colors if str(c).strip()]
                size_filter = str(filters.get('size', '')).strip().lower() if filters.get('size') else None

                def price_in_range(v):
                    try:
                        p = float(v.get('price')) if v.get('price') is not None else None
                    except ValueError:
                        return False if (price_min_val is not None or price_max_val is not None) else True
                    if price_min_val is not None and p is not None and p < price_min_val:
                        return False
                    if price_max_val is not None and p is not None and p > price_max_val:
                        return False
                    return True

                def matches_colors(v, product_title: str):
                    if not colors:
                        return True
                    vt = (v.get('title') or '').lower()
                    pt = (product_title or '').lower()
                    return any(c in vt or c in pt for c in colors)

                def matches_size(v):
                    if not size_filter:
                        return True
                    vt = (v.get('title') or '').lower()
                    return size_filter in vt

                def matches_sale(v):
                    if not on_sale:
                        return True
                    try:
                        price = float(v.get('price')) if v.get('price') not in (None, "") else None
                        cap = float(v.get('compare_at_price')) if v.get('compare_at_price') not in (None, "") else None
                        return price is not None and cap is not None and cap > price
                    except ValueError:
                        return False

                filtered_variants = [
                    v for v in variants
                    if price_in_range(v)
                    and matches_colors(v, node.get('title'))
                    and matches_size(v)
                    and matches_sale(v)
                ]

                if not filtered_variants:
                    continue
                products.append({
                    "id": node.get('id'),
                    "title": node.get('title'),
                    "handle": handle,
                    "url": online_url,
                    "image": image,
                    "variants": filtered_variants
                })
        return {"products": products, "query": q}

    def list_recent_orders(self, limit: int = 5):
        """List recent orders to help locate a valid order number for testing"""
        gql = """
        query($first: Int!) {
          orders(first: $first, sortKey: PROCESSED_AT, reverse: true) {
            edges {
              node {
                id
                name
                processedAt
                displayFulfillmentStatus
              }
            }
          }
        }
        """
        data = self._graphql(gql, {"first": max(1, min(limit, 25))})
        if "error" in data:
            return data
        edges = (((data or {}).get('orders') or {}).get('edges')) if isinstance(data, dict) else None
        orders = []
        if edges:
            for edge in edges:
                node = edge.get('node', {})
                # name typically contains the display order number like #1001
                orders.append({
                    "id": node.get('id'),
                    "name": node.get('name'),
                    "order_number_hint": node.get('name'),
                    "processed_at": node.get('processedAt'),
                    "fulfillment_status": node.get('displayFulfillmentStatus')
                })
        return {"orders": orders}

# Initialize Shopify client
shopify_client = ShopifyAPIClient()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Reamaze API Bridge",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    """Create a support ticket in Reamaze"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_email', 'issue_summary']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Extract data
        customer_email = data['customer_email']
        customer_name = data.get('customer_name', customer_email)
        issue_summary = data['issue_summary']
        order_number = data.get('order_number')
        
        # Create ticket subject and body
        subject = f"Support Request: {issue_summary}"
        body_parts = [
            f"Customer: {customer_name}",
            f"Email: {customer_email}",
            f"Issue: {issue_summary}"
        ]
        
        if order_number:
            body_parts.append(f"Order Number: {order_number}")
        
        body = "\n".join(body_parts)
        
        # Create conversation via Reamaze API
        result = reamaze_client.create_conversation(
            subject=subject,
            body=body,
            customer_email=customer_email,
            customer_name=customer_name
        )
        
        if "error" in result:
            logger.error(f"Failed to create ticket: {result['error']}")
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        logger.info(f"Successfully created ticket for {customer_email}")
        
        # Extract ticket identifier - use slug if no numeric ID available
        ticket_id = result.get("id") or result.get("conversation", {}).get("id") or result.get("slug")
        
        return jsonify({
            "success": True,
            "message": "Support ticket created successfully",
            "ticket_id": ticket_id,
            "ticket_slug": result.get("slug"),  # Always provide slug as backup
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/search-kb', methods=['POST'])
def search_knowledge_base():
    """Search knowledge base articles"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('query_term'):
            return jsonify({
                "success": False,
                "error": "Missing required field: query_term"
            }), 400
        
        query_term = data['query_term']
        max_results = data.get('max_results', 5)
        
        # Search articles
        result = reamaze_client.search_articles(query_term, max_results)
        
        if "error" in result:
            logger.error(f"Failed to search knowledge base: {result['error']}")
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        # Process results
        articles = []
        if isinstance(result, dict) and 'articles' in result:
            for article in result['articles'][:max_results]:
                articles.append({
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "slug": article.get("slug"),
                    "body": article.get("body", "")[:300] + "..." if len(article.get("body", "")) > 300 else article.get("body", ""),
                    "url": article.get("url")
                })
        
        logger.info(f"Found {len(articles)} articles for query: {query_term} (total in KB: {result.get('total_count', 'unknown')})")
        return jsonify({
            "success": True,
            "query": query_term,
            "count": len(articles),
            "total_articles_in_kb": result.get('total_count', 0),
            "articles": articles
        })
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/get-instructions', methods=['POST'])
def get_instructions():
    """Get step-by-step instructions from knowledge base"""
    try:
        data = request.get_json()
        
        # Validate input
        topic = data.get('topic')
        article_id = data.get('article_id')
        
        if not topic and not article_id:
            return jsonify({
                "success": False,
                "error": "Either 'topic' or 'article_id' must be provided"
            }), 400
        
        # Get article by ID or search for topic
        if article_id:
            result = reamaze_client.get_article(article_id)
        else:
            # Search for the topic and get the first result
            search_result = reamaze_client.search_articles(topic, 1)
            if "error" in search_result:
                return jsonify({
                    "success": False,
                    "error": search_result["error"]
                }), search_result.get("status_code", 500)
            
            # Check if articles were found
            if not isinstance(search_result, dict) or 'articles' not in search_result:
                return jsonify({
                    "success": False,
                    "error": "Invalid response from API"
                }), 500
            
            articles = search_result.get("articles", [])
            if not articles or len(articles) == 0:
                return jsonify({
                    "success": False,
                    "error": f"No articles found for topic: {topic}"
                }), 404
            
            result = articles[0]
        
        if "error" in result:
            logger.error(f"Failed to get instructions: {result['error']}")
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        # Extract instructions
        instructions = {
            "id": result.get("id"),
            "title": result.get("title"),
            "content": result.get("body", ""),
            "slug": result.get("slug"),
            "url": result.get("url")
        }
        
        logger.info(f"Retrieved instructions for: {topic or article_id}")
        return jsonify({
            "success": True,
            "instructions": instructions
        })
        
    except Exception as e:
        logger.error(f"Error getting instructions: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/get-previous-conversations', methods=['POST'])
def get_previous_conversations():
    """Retrieve previous conversations for a customer"""
    try:
        data = request.get_json()
        
        # Validate input - need either email or order_number
        customer_email = data.get('customer_email')
        order_number = data.get('order_number')
        limit = data.get('limit', 10)  # Default to 10 conversations
        
        if not customer_email and not order_number:
            return jsonify({
                "success": False,
                "error": "Either 'customer_email' or 'order_number' must be provided"
            }), 400
        
        # Search conversations
        if customer_email:
            result = reamaze_client.get_conversations(for_email=customer_email, limit=limit)
        else:
            # Search by order number in conversation content
            result = reamaze_client.get_conversations(q=order_number, limit=limit)
        
        if "error" in result:
            logger.error(f"Failed to retrieve conversations: {result['error']}")
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        # Process conversations
        conversations = []
        if isinstance(result, dict) and 'conversations' in result:
            for conv in result['conversations']:
                # Extract customer email from author or followers
                customer_email = None
                if conv.get("author", {}).get("email"):
                    customer_email = conv["author"]["email"]
                elif conv.get("followers") and len(conv["followers"]) > 0:
                    # Get the first customer's email from followers
                    for follower in conv["followers"]:
                        if follower.get("customer?", False):
                            customer_email = follower.get("email")
                            break
                
                # Extract last message snippet
                last_message_snippet = ""
                if conv.get("last_customer_message", {}).get("body"):
                    body = conv["last_customer_message"]["body"]
                    last_message_snippet = body[:100] + "..." if len(body) > 100 else body
                
                conversations.append({
                    "id": None,  # Reamaze conversations don't have numeric IDs
                    "slug": conv.get("slug"),  # Slug is the primary identifier
                    "subject": conv.get("subject"),
                    "status": conv.get("status"),
                    "status_text": STATUS_CODES.get(conv.get("status"), "Unknown"),
                    "origin": conv.get("origin"),
                    "origin_text": ORIGIN_CODES.get(conv.get("origin"), "Unknown"),
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "assignee": conv.get("assignee", {}).get("name") if conv.get("assignee") else None,
                    "customer_email": customer_email,
                    "message_count": conv.get("message_count", 0),
                    "last_message_snippet": last_message_snippet
                })
        
        search_type = "email" if customer_email else "order_number"
        search_value = customer_email or order_number
        
        logger.info(f"Found {len(conversations)} conversations for {search_type}: {search_value}")
        return jsonify({
            "success": True,
            "search_type": search_type,
            "search_value": search_value,
            "count": len(conversations),
            "conversations": conversations
        })
        
    except Exception as e:
        logger.error(f"Error retrieving previous conversations: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/check-ticket-status', methods=['POST'])
def check_ticket_status():
    """Check the status of a specific ticket/conversation"""
    try:
        data = request.get_json()
        
        # Validate required field
        ticket_id = data.get('ticket_id')
        
        if not ticket_id:
            return jsonify({
                "success": False,
                "error": "Missing required field: ticket_id"
            }), 400
        
        # Get conversation details
        result = reamaze_client.get_conversation(ticket_id)
        
        if "error" in result:
            logger.error(f"Failed to get ticket status: {result['error']}")
            # Check for 404 in error message if status_code not set
            if result.get("status_code") == 404 or "404" in str(result.get("error", "")):
                return jsonify({
                    "success": False,
                    "error": f"Ticket not found: {ticket_id}"
                }), 404
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        # Extract key ticket information
        ticket_info = {
            "id": result.get("id"),
            "slug": result.get("slug"),
            "subject": result.get("subject"),
            "status": result.get("status"),
            "status_text": STATUS_CODES.get(result.get("status"), "Unknown"),
            "origin": result.get("origin"),
            "origin_text": ORIGIN_CODES.get(result.get("origin"), "Unknown"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "category": result.get("category"),
            "assignee": {
                "name": result.get("assignee", {}).get("name"),
                "email": result.get("assignee", {}).get("email")
            } if result.get("assignee") else None,
            "customer": {
                "name": result.get("user", {}).get("name"),
                "email": result.get("user", {}).get("email")
            } if result.get("user") else None,
            "message_count": len(result.get("messages", [])),
            "tags": result.get("tags", []),
            "messages": []  # Initialize messages list
        }
        
        # Process all messages for conversation history
        messages = result.get("messages", [])
        if messages:
            for message in messages:
                author_name = "Unknown"
                if message.get("user"):
                    author_name = message["user"].get("name", message["user"].get("email", "Unknown"))
                
                ticket_info["messages"].append({
                    "body": message.get("body"),
                    "created_at": message.get("created_at"),
                    "author_name": author_name,
                    "author_type": "staff" if message.get("visible_to_customer") is False else "customer"
                })

            # If top-level customer is null, try to find it from messages
            if not ticket_info["customer"] and any(msg["author_type"] == "customer" for msg in ticket_info["messages"]):
                first_customer_msg = next((msg for msg in messages if msg.get("user") and msg.get("visible_to_customer") is not False), None)
                if first_customer_msg:
                    ticket_info["customer"] = {
                        "name": first_customer_msg["user"].get("name"),
                        "email": first_customer_msg["user"].get("email")
                    }

            # If top-level assignee is null, try to find it from staff messages
            if not ticket_info["assignee"] and any(msg["author_type"] == "staff" for msg in ticket_info["messages"]):
                first_staff_msg = next((msg for msg in messages if msg.get("user") and msg.get("visible_to_customer") is False), None)
                if first_staff_msg:
                     ticket_info["assignee"] = {
                        "name": first_staff_msg["user"].get("name"),
                        "email": first_staff_msg["user"].get("email")
                    }

        logger.info(f"Retrieved ticket status for ID: {ticket_id}")
        return jsonify({
            "success": True,
            "ticket": ticket_info
        })
        
    except Exception as e:
        logger.error(f"Error checking ticket status: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/add-ticket-info', methods=['POST'])
def add_ticket_info():
    """Add new information to an existing ticket/conversation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['ticket_id', 'message', 'customer_email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        ticket_id = data['ticket_id']
        message = data['message']
        customer_email = data['customer_email']
        customer_name = data.get('customer_name', customer_email)
        
        # First, verify the ticket exists
        existing_ticket = reamaze_client.get_conversation(ticket_id)
        
        if "error" in existing_ticket:
            if existing_ticket.get("status_code") == 404 or "404" in str(existing_ticket.get("error", "")):
                return jsonify({
                    "success": False,
                    "error": f"Ticket not found: {ticket_id}"
                }), 404
            return jsonify({
                "success": False,
                "error": existing_ticket["error"]
            }), existing_ticket.get("status_code", 500)
        
        # Add message to the conversation
        result = reamaze_client.add_message_to_conversation(
            conversation_id=ticket_id,
            body=message,
            author_email=customer_email,
            author_name=customer_name
        )
        
        if "error" in result:
            logger.error(f"Failed to add message to ticket {ticket_id}: {result['error']}")
            return jsonify({
                "success": False,
                "error": result["error"]
            }), result.get("status_code", 500)
        
        logger.info(f"Successfully added message to ticket {ticket_id} from {customer_email}")
        return jsonify({
            "success": True,
            "message": "Information added to ticket successfully",
            "ticket_id": ticket_id,
            "message_id": result.get("id") or result.get("message", {}).get("id"),
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error adding information to ticket: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ==========================
# Shopify Endpoints
# ==========================

@app.route('/track-order', methods=['POST'])
def track_order():
    """Track an order by order number (e.g., 1001 or #1001) via Shopify Admin GraphQL"""
    try:
        data = request.get_json() or {}
        order_number = str(data.get('order_number', '')).strip()
        if not order_number:
            return jsonify({
                "success": False,
                "error": "Missing required field: order_number"
            }), 400

        order = shopify_client.get_order_by_number(order_number)
        if not order:
            return jsonify({
                "success": False,
                "error": f"Order not found: {order_number}"
            }), 404

        # Normalize output
        fulfillments = []
        for f in (order.get('fulfillments') or []):
            tracking = []
            for t in (f.get('trackingInfo') or []):
                tracking.append({
                    "number": t.get('number'),
                    "url": t.get('url'),
                    "company": t.get('company')
                })
            fulfillments.append({
                "created_at": f.get('createdAt'),
                "status": f.get('status'),
                "tracking": tracking
            })

        items = []
        for edge in (order.get('lineItems', {}).get('edges') or []):
            node = edge.get('node', {})
            variant = node.get('variant') or {}
            product = (variant.get('product') or {})
            items.append({
                "name": node.get('name'),
                "quantity": node.get('quantity'),
                "sku": node.get('sku'),
                "variant_title": variant.get('title'),
                "product_title": product.get('title'),
                "product_url": product.get('onlineStoreUrl'),
                "variant_image": (variant.get('image') or {}).get('url')
            })

        return jsonify({
            "success": True,
            "order": {
                "id": order.get('id'),
                "name": order.get('name'),
                "order_number": order.get('orderNumber'),
                "processed_at": order.get('processedAt'),
                "closed_at": order.get('closedAt'),
                "cancelled_at": order.get('cancelledAt'),
                "financial_status": order.get('displayFinancialStatus'),
                "fulfillment_status": order.get('displayFulfillmentStatus'),
                "customer": order.get('customer'),
                "shipping_address": order.get('shippingAddress'),
                "fulfillments": fulfillments,
                "items": items
            }
        })
    except Exception as e:
        logger.error(f"Error tracking order: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@app.route('/recommend-products', methods=['POST'])
def recommend_products():
    """Return product recommendations based on structured filters and/or a query string.

    Expected JSON body (flexible):
      {
        "query_text": "apple watch strap",
        "filters": {
          "watch_model": "Series 7",
          "size": "45mm",
          "material": "leather",
          "color": "black"
        },
        "limit": 5
      }
    """
    try:
        data = request.get_json() or {}
        query_text = data.get('query_text')
        limit = int(data.get('limit', 5))

        # Accept flat one-level JSON; merge with optional legacy nested 'filters'
        flat_keys = [
            'product_type', 'vendor', 'tag',
            'watch_model', 'size', 'material', 'color', 'colors',
            'price_min', 'price_max', 'on_sale'
        ]
        filters = {k: data.get(k) for k in flat_keys if k in data}

        # Normalize color(s)
        if 'color' in filters and 'colors' not in filters:
            filters['colors'] = [filters.pop('color')]
        elif 'colors' in filters and isinstance(filters['colors'], str):
            filters['colors'] = [filters['colors']]

        # Merge legacy nested filters if provided (flat keys take precedence)
        legacy_filters = data.get('filters', {}) if isinstance(data.get('filters'), dict) else {}
        merged_filters = {**legacy_filters, **filters}

        result = shopify_client.search_products(query_text=query_text, filters=merged_filters, limit=limit)
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Unknown error')
            }), result.get('status_code', 500)

        return jsonify({
            "success": True,
            "query": result.get('query'),
            "count": len(result.get('products', [])),
            "products": result.get('products', [])
        })
    except Exception as e:
        logger.error(f"Error recommending products: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

if app.config.get('DEBUG', False):
    @app.route('/list-recent-orders', methods=['GET'])
    def list_recent_orders():
        """Helper endpoint: list recent Shopify order names/numbers for testing (DEBUG only)"""
        try:
            limit = int(request.args.get('limit', 5))
            result = shopify_client.list_recent_orders(limit=limit)
            if "error" in result:
                return jsonify({
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }), result.get('status_code', 500)
            return jsonify({
                "success": True,
                "count": len(result.get('orders', [])),
                "orders": result.get('orders', [])
            })
        except Exception as e:
            logger.error(f"Error listing recent orders: {e}")
            return jsonify({
                "success": False,
                "error": "Internal server error"
            }), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000) 