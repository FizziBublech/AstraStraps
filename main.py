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
        return jsonify({
            "success": True,
            "message": "Support ticket created successfully",
            "ticket_id": result.get("id"),
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