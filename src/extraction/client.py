import os
from google.cloud import language_v1
from google.auth.exceptions import DefaultCredentialsError

class LangExtractClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LangExtractClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, credentials_path=None, api_key=None):
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.api_key = api_key
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            if self.api_key:
                # Initialize client with API key if applicable
                pass
            else:
                self.client = language_v1.LanguageServiceClient()
        except DefaultCredentialsError as e:
            print(f"Failed to initialize client: {e}")

    def extract_language_features(self, text):
        if not self.client:
            raise Exception("Client is not initialized.")

        try:
            document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
            response = self.client.analyze_entities(request={'document': document})
            return response
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None
