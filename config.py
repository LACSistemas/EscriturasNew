"""Application configuration and client initialization"""
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google.cloud import vision
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Flask configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Session storage (in-memory)
sessions: Dict[str, Dict[str, Any]] = {}


class Config:
    """Application configuration and client management"""

    def __init__(self):
        self.vision_client: Optional[vision.ImageAnnotatorClient] = None
        self.gemini_model = None
        self.logger = logging.getLogger(__name__)

    def initialize_vision_client(self) -> bool:
        """Initialize Google Cloud Vision client"""
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.logger.info("Google Cloud Vision client initialized successfully")
            return True
        except Exception as e:
            self.logger.warning(f"Google Cloud Vision client failed to initialize: {e}")
            self.logger.warning("Vision OCR will not be available, but app will continue running")
            return False

    def initialize_gemini_client(self) -> bool:
        """Initialize Gemini AI client"""
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.logger.info("Gemini AI client initialized successfully")
                return True
            else:
                self.logger.warning("GEMINI_API_KEY not found in environment")
                return False
        except Exception as e:
            self.logger.warning(f"Gemini AI client failed to initialize: {e}")
            return False

    def get_vision_client(self) -> Optional[vision.ImageAnnotatorClient]:
        """Get the Vision client instance"""
        return self.vision_client

    def get_gemini_model(self):
        """Get the Gemini model instance"""
        return self.gemini_model


# Global config instance
config = Config()
