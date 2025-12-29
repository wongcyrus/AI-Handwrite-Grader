import os
import pytest
from dotenv import load_dotenv

def pytest_configure(config):
    """Load environment variables for tests"""
    # Load from the app/.env file
    env_path = os.path.join(os.path.dirname(__file__), 'app', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from: {env_path}")
    else:
        print(f"Environment file not found: {env_path}")
