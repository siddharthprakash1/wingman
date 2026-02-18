import os

def get_credentials_path():
    return os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)

def get_api_key():
    return os.getenv('LANGEXTRACT_API_KEY', None)
