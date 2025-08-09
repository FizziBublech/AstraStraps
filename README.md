# Reamaze API Bridge

A Flask application that acts as a lightweight API bridge between chatbots and the Reamaze API. This app provides simplified RESTful endpoints for creating support tickets, searching knowledge base articles, and retrieving step-by-step instructions.

## Features

- **Support Ticket Creation**: Create support tickets for unresolved issues
- **Knowledge Base Search**: Search articles for self-service support
- **Step-by-Step Instructions**: Retrieve detailed instructions from knowledge base
- **Rate Limiting**: Built-in retry logic and rate limit handling
- **Error Handling**: Comprehensive error handling with detailed logging
- **Security**: HTTP Basic Auth with Reamaze API token

## Quick Start

### Prerequisites

- Python 3.7+
- Reamaze account with API access
- API token from Reamaze

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd reamaze-api-bridge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Reamaze credentials
```

4. Run the application:
```bash
python main.py
```

The app will be available at `http://localhost:5000`

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Reamaze API Configuration
REAMAZE_SUBDOMAIN=your-subdomain  # Without .reamaze.com
REAMAZE_API_TOKEN=your-api-token-here

# Flask Configuration
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_RETRIES=3
RATE_LIMIT_DELAY=60
```

## API Endpoints

### Health Check

**GET /** 

Returns the service status and timestamp.

**Response:**
```json
{
  "status": "healthy",
  "service": "Reamaze API Bridge",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Create Support Ticket

**POST /create-ticket**

Creates a new support ticket in Reamaze.

**Request Body:**
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "issue_summary": "Unable to track my order",
  "order_number": "12345"
}
```

**Required Fields:**
- `customer_email`: Customer's email address
- `issue_summary`: Brief description of the issue

**Optional Fields:**
- `customer_name`: Customer's name (defaults to email)
- `order_number`: Order number if applicable

**Response:**
```json
{
  "success": true,
  "message": "Support ticket created successfully",
  "ticket_id": "12345",
  "data": { ... }
}
```

### Search Knowledge Base

**POST /search-kb**

Searches the Reamaze knowledge base for articles.

**Request Body:**
```json
{
  "query_term": "apple watch band sizing",
  "max_results": 5
}
```

**Required Fields:**
- `query_term`: Search query

**Optional Fields:**
- `max_results`: Maximum number of results (default: 5)

**Response:**
```json
{
  "success": true,
  "query": "apple watch band sizing",
  "count": 0,
  "total_articles_in_kb": 0,
  "articles": []
}
```

**Note**: Currently returns empty results as the knowledge base contains 0 articles. Once articles are added to Reamaze, this endpoint will return populated results.

### Get Instructions

**POST /get-instructions**

Retrieves step-by-step instructions from the knowledge base.

**Request Body:**
```json
{
  "topic": "install band"
}
```

**OR**

```json
{
  "article_id": "123"
}
```

**Required Fields:**
- Either `topic` OR `article_id` must be provided

**Response** (when articles exist):
```json
{
  "success": true,
  "instructions": {
    "id": "123",
    "title": "How to Install Your Band",
    "content": "Step-by-step instructions...",
    "slug": "install-band",
    "url": "https://example.com/article"
  }
}
```

**Current Response** (knowledge base empty):
```json
{
  "success": false,
  "error": "No articles found for topic: install band"
}
```
**HTTP Status**: 404

### Get Previous Conversations

**POST /get-previous-conversations**

Retrieves previous support conversations for a customer by email or order number.

**Request Body:**
```json
{
  "customer_email": "customer@example.com",
  "limit": 10
}
```

**OR**

```json
{
  "order_number": "12345",
  "limit": 10
}
```

**Required Fields:**
- Either `customer_email` OR `order_number` must be provided

**Optional Fields:**
- `limit`: Maximum number of conversations to return (default: 10)

**Response:**
```json
{
  "success": true,
  "search_type": "email",
  "search_value": "customer@example.com",
  "count": 3,
  "conversations": [
    {
      "id": null,
      "slug": "support-request-shipping-issue-abc123",
      "subject": "Support Request: Shipping Issue",
      "status": 0,
      "status_text": "Unresolved",
      "origin": 7,
      "origin_text": "API",
      "created_at": "2025-07-10T12:00:00.000Z",
      "updated_at": "2025-07-10T14:00:00.000Z",
      "assignee": "John Doe",
      "customer_email": "customer@example.com",
      "message_count": 3,
      "last_message_snippet": "Thank you for reaching out about your order..."
    }
  ]
}
```

**Important Note**: Reamaze conversations don't have numeric IDs - they use slugs as the primary identifier. Use the `slug` field when calling other endpoints like `/check-ticket-status` or `/add-ticket-info`.

### Check Ticket Status

**POST /check-ticket-status**

Retrieves detailed status information for a specific support ticket.

**Request Body:**
```json
{
  "ticket_id": "support-request-shipping-issue-abc123"
}
```

**Required Fields:**
- `ticket_id`: The slug/identifier of the ticket to check (not a numeric ID)

**Response:**
```json
{
  "success": true,
  "ticket": {
    "id": null,
    "slug": "support-request-shipping-issue-abc123",
    "subject": "Support Request: Shipping Issue",
    "status": 0,
    "status_text": "Unresolved",
    "origin": 7,
    "origin_text": "API",
    "created_at": "2025-07-10T12:00:00.000Z",
    "updated_at": "2025-07-10T14:00:00.000Z",
    "category": {
      "channel": 1,
      "email": "support@astrastraps.com",
      "name": "Astra Straps",
      "slug": "astra-straps"
    },
    "assignee": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "customer": {
      "name": "Jane Smith",
      "email": "customer@example.com"
    },
    "message_count": 2,
    "tags": ["urgent", "shipping"],
    "messages": [
      {
        "body": "Hello, I'm having an issue with my recent order. Can you help?",
        "created_at": "2025-07-10T12:00:00.000Z",
        "author_name": "Jane Smith",
        "author_type": "customer"
      },
      {
        "body": "We have investigated your shipping issue and found...",
        "created_at": "2025-07-10T14:00:00.000Z",
        "author_name": "John Doe",
        "author_type": "staff"
      }
    ]
  }
}
```

**Note on `assignee` and `customer` fields**: If these fields are not available at the top level of the ticket data, the system will attempt to populate them from the first staff and customer messages in the conversation history.

**Status Codes:**
- `0`: Open/Unresolved
- `2`: Resolved/Closed  
- `5`: Archived

**Human-Readable Fields:**
- `status_text`: Human-readable version of the status code (e.g., "Unresolved", "Resolved", "Pending")
- `origin_text`: Human-readable version of origin code (e.g., "API", "Email", "Chat")

**Complete Status Mapping:**
- `0`: Unresolved
- `1`: Pending
- `2`: Resolved
- `3`: Spam
- `4`: Archived
- `5`: On Hold
- `6`: Auto-Resolved
- `7`: Chatbot Assigned
- `8`: Chatbot Resolved
- `9`: Spam - identified by AI

**Complete Origin Mapping:**
- `0`: Chat
- `1`: Email
- `2`: Twitter
- `3`: Facebook
- `6`: Classic Mode Chat
- `7`: API
- `8`: Instagram
- `9`: SMS
- `15`: WhatsApp
- `16`: Staff Outbound
- `17`: Contact Form

### Add Information to Existing Ticket

**POST /add-ticket-info**

Adds additional information or updates to an existing support ticket.

**Request Body:**
```json
{
  "ticket_id": "support-request-shipping-issue-abc123",
  "message": "I found additional information about my issue. The problem occurs when...",
  "customer_email": "customer@example.com",
  "customer_name": "Jane Smith"
}
```

**Required Fields:**
- `ticket_id`: The slug/identifier of the existing ticket to update (not a numeric ID)
- `message`: The additional information or update to add
- `customer_email`: Customer's email address

**Optional Fields:**
- `customer_name`: Customer's name (defaults to email)

**Response:**
```json
{
  "success": true,
  "message": "Information added to ticket successfully",
  "ticket_id": "12345",
  "message_id": "67890",
  "data": { ... }
}
```

**Error Responses:**
- `404`: Ticket not found
- `400`: Missing required fields
- `500`: Internal server error

### Track Order (Shopify)

**POST /track-order**

Find and return order status and tracking details by order number (e.g., `1001` or `#1001`).

Shopify Admin API credentials must be configured.

**Request Body:**
```json
{
  "order_number": "1001"
}
```

**Response:**
```json
{
  "success": true,
  "order": {
    "id": "gid://shopify/Order/1234567890",
    "name": "#1001",
    "order_number": 1001,
    "processed_at": "2025-07-10T12:00:00Z",
    "closed_at": null,
    "cancelled_at": null,
    "financial_status": "PAID",
    "fulfillment_status": "PARTIALLY_FULFILLED",
    "customer": {
      "displayName": "Jane Smith",
      "email": "customer@example.com"
    },
    "shipping_address": { "name": "Jane Smith", "city": "Austin", "country": "US", "zip": "78701" },
    "fulfillments": [
      {
        "created_at": "2025-07-11T10:00:00Z",
        "status": "SUCCESS",
        "tracking": [ { "number": "1Z...", "url": "https://...", "company": "UPS" } ]
      }
    ],
    "items": [
      {
        "name": "Leather Strap - 45mm",
        "quantity": 1,
        "sku": "ASTRA-LE-45-BLK",
        "variant_title": "Black / 45mm",
        "product_title": "Leather Strap",
        "product_url": "https://your-shop.myshopify.com/products/leather-strap",
        "variant_image": "https://cdn.shopify.com/...jpg"
      }
    ]
  }
}
```

**Errors:**
- `400`: Missing `order_number`
- `404`: Order not found
- `500`: Internal server error

### Recommend Products (Shopify)

**POST /recommend-products**

Return product recommendations based on free-text query and/or structured filters. Designed for chatbot use; provide as much context as available.

**Request Body (example):**
```json
{
  "query_text": "apple watch strap",
  "watch_model": "Series 7",
  "size": "45mm",
  "material": "leather",
  "color": "black",
  "price_min": 20,
  "price_max": 40,
  "on_sale": true,
  "limit": 5
}
```

**Response:**
```json
{
  "success": true,
  "query": "apple watch strap title:Series 7 tag:\"Series 7\" title:45mm tag:\"45mm\" title:leather tag:\"leather\" title:black tag:\"black\"",
  "count": 2,
  "products": [
    {
      "id": "gid://shopify/Product/123",
      "title": "Leather Strap",
      "handle": "leather-strap",
      "url": "https://your-shop.myshopify.com/products/leather-strap",
      "image": "https://cdn.shopify.com/...jpg",
      "variants": [
        {
          "id": "gid://shopify/ProductVariant/111",
          "title": "Black / 45mm",
          "sku": "ASTRA-LE-45-BLK",
          "price": "39.00",
          "compare_at_price": "49.00",
          "currency": "USD",
          "image": "https://cdn.shopify.com/...variant.jpg",
          "url": "https://your-shop.myshopify.com/products/leather-strap?variant=111"
        }
      ]
    }
  ]
}
```

**Errors:**
- `500`: Internal server error

### When to use these endpoints

- `track-order`:
  - When the user provides an order number or asks for order status/tracking.
  - Ask for the order number (with or without a leading `#`). If needed, optionally confirm the shipping ZIP for safety.
  - Returns status, customer/shipping, line items, and tracking links if available.

- `recommend-products`:
  - When the user requests product suggestions or asks for options by material, color, size, model, budget, or “on sale”.
  - Collect: `watch_model`, `size` (41/45/49mm), `material`, `color/colors`, `price_max` (or `price_min` and `price_max`), `on_sale`.
  - Returns product list with variant-level `image` and deep `url` (including `?variant=`), so the exact option opens on the PDP.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing required fields)
- `404`: Not Found (article not found)
- `429`: Rate Limited
- `500`: Internal Server Error

## Testing

### Manual Testing with cURL

1. **Health Check:**
```bash
curl http://localhost:5000/
```

2. **Search Knowledge Base:**
```bash
curl -X POST http://localhost:5000/search-kb \
  -H "Content-Type: application/json" \
  -d '{
    "query_term": "sizing guide",
    "max_results": 3
  }'
```

3. **Get Instructions:**
```bash
curl -X POST http://localhost:5000/get-instructions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "installation guide"
  }'
```

⚠️ **Important**: 
- **Ticket Creation**: ✅ Fully working - creates real tickets in your Reamaze "Astra Straps" channel
- **Knowledge Base**: Currently empty (0 articles) - searches will return empty results until articles are added
- **All endpoints tested and verified working** as of July 2025

## Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Environment Variables for Production

Set these environment variables in your production environment:

```bash
export REAMAZE_SUBDOMAIN=your-subdomain
export REAMAZE_API_TOKEN=your-production-token
export FLASK_DEBUG=False
export SECRET_KEY=your-secure-secret-key
export LOG_LEVEL=WARNING
export SHOPIFY_STORE_DOMAIN=rtoprcostmetics.myshopify.com
export SHOPIFY_ADMIN_TOKEN=shpat_...
export SHOPIFY_API_VERSION=2024-10
```

### Deployment Platforms

This app is ready for deployment on:
- Render
- Heroku
- AWS Elastic Beanstalk
- Google App Engine
- Any Docker-compatible platform

## Chatbot Integration

### Quick Reference - JSON Formats

**Create Support Ticket** (POST /create-ticket):
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "issue_summary": "Cannot track my order",
  "order_number": "12345"
}
```

**Search Knowledge Base** (POST /search-kb):
```json
{
  "query_term": "apple watch sizing",
  "max_results": 5
}
```

**Get Instructions** (POST /get-instructions):
```json
{
  "topic": "installation guide"
}
```

**Get Previous Conversations** (POST /get-previous-conversations):
```json
{
  "customer_email": "customer@example.com",
  "limit": 10
}
```

**OR**

```json
{
  "order_number": "12345",
  "limit": 10
}
```

**Check Ticket Status** (POST /check-ticket-status):
```json
{
  "ticket_id": "support-request-shipping-issue-abc123"
}
```

**Add Information to Ticket** (POST /add-ticket-info):
```json
{
  "ticket_id": "support-request-shipping-issue-abc123",
  "message": "Additional information about my issue...",
  "customer_email": "customer@example.com",
  "customer_name": "John Doe"
}
```

### Python Integration Example

```python
import requests

# Search knowledge base
response = requests.post('http://your-api-url/search-kb', json={
    'query_term': 'user question',
    'max_results': 3
})

if response.json()['success']:
    articles = response.json()['articles']
    # Process articles for chatbot response
else:
    # Handle empty knowledge base or errors
    print("No articles found or error occurred")

# Create support ticket
ticket_response = requests.post('http://your-api-url/create-ticket', json={
    'customer_email': 'user@example.com',
    'customer_name': 'User Name',
    'issue_summary': 'Need help with product'
})

if ticket_response.json()['success']:
    print("Support ticket created successfully!")

# Get previous conversations by email
conversations_response = requests.post('http://your-api-url/get-previous-conversations', json={
    'customer_email': 'user@example.com',
    'limit': 5
})

# OR get previous conversations by order number
conversations_response = requests.post('http://your-api-url/get-previous-conversations', json={
    'order_number': '12345',
    'limit': 5
})
```

## Rate Limiting

The app includes built-in rate limiting protection:
- Automatic retries on rate limit (429) responses
- Exponential backoff for failed requests
- Configurable retry attempts and delays

## Logging

All requests and errors are logged with the following format:
```
2024-01-01 12:00:00 - main - INFO - Making GET request to https://subdomain.reamaze.com/api/articles
```

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Security

- API token stored in environment variables
- HTTPS-only communication with Reamaze
- Input validation on all endpoints
- Request timeout protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your environment variables are set correctly
3. Test with the Reamaze API directly to confirm credentials
4. Create an issue in the repository 