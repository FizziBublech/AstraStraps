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

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000) 