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
  "count": 3,
  "articles": [
    {
      "id": "123",
      "title": "Apple Watch Band Sizing Guide",
      "slug": "apple-watch-band-sizing",
      "body": "Complete guide to sizing...",
      "url": "https://example.com/article"
    }
  ]
}
```

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

**Response:**
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

⚠️ **Important**: Only test read-only endpoints (search-kb, get-instructions) with the live API. Do not create test tickets in the production system.

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
```

### Deployment Platforms

This app is ready for deployment on:
- Render
- Heroku
- AWS Elastic Beanstalk
- Google App Engine
- Any Docker-compatible platform

## Chatbot Integration

Your chatbot can integrate with this API using simple HTTP requests:

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