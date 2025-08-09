import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Reamaze API Configuration
    REAMAZE_SUBDOMAIN = os.environ.get('REAMAZE_SUBDOMAIN', 'bodwellness')
    REAMAZE_API_TOKEN = os.environ.get('REAMAZE_API_TOKEN')
    REAMAZE_EMAIL = os.environ.get('REAMAZE_EMAIL')
    REAMAZE_BASE_URL = f"https://{REAMAZE_SUBDOMAIN}.reamaze.io/api/v1"
    
    # Rate limiting configuration
    RATE_LIMIT_RETRIES = int(os.environ.get('RATE_LIMIT_RETRIES', '3'))
    RATE_LIMIT_DELAY = int(os.environ.get('RATE_LIMIT_DELAY', '60'))  # seconds
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Shopify Admin API Configuration (optional but required for Shopify endpoints)
    SHOPIFY_STORE_DOMAIN = os.environ.get('SHOPIFY_STORE_DOMAIN')  # e.g. rtoprcostmetics.myshopify.com
    SHOPIFY_ADMIN_TOKEN = os.environ.get('SHOPIFY_ADMIN_TOKEN')  # Admin API access token (starts with shpat_)
    SHOPIFY_API_VERSION = os.environ.get('SHOPIFY_API_VERSION', '2024-10')
    SHOPIFY_ADMIN_REST_BASE_URL = (
        f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}"
        if SHOPIFY_STORE_DOMAIN else None
    )
    SHOPIFY_ADMIN_GRAPHQL_URL = (
        f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        if SHOPIFY_STORE_DOMAIN else None
    )
    
    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        required_vars = ['REAMAZE_API_TOKEN', 'REAMAZE_EMAIL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Shopify variables are optional overall, but both are required if either is set
        has_any_shopify = any([
            os.environ.get('SHOPIFY_STORE_DOMAIN'),
            os.environ.get('SHOPIFY_ADMIN_TOKEN')
        ])
        if has_any_shopify:
            shopify_missing = [
                var for var in ['SHOPIFY_STORE_DOMAIN', 'SHOPIFY_ADMIN_TOKEN']
                if not os.environ.get(var)
            ]
            if shopify_missing:
                raise ValueError(
                    "Shopify configuration incomplete. Missing: " + ', '.join(shopify_missing)
                )
        
        return True 