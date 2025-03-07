from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY")
    
settings = Settings()