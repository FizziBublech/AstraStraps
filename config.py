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
    
    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        required_vars = ['REAMAZE_API_TOKEN', 'REAMAZE_EMAIL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True 