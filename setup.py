# automated_skeptic_mvp/setup.py
"""
Setup script for Automated Skeptic MVP
"""

import os
import subprocess
import sys
from data.sample_claims import save_test_claims_csv

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        'data',
        'config',
        'logs',
        'tests',
        'agents',
        'pipeline',
        'apis'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error installing dependencies. Please install manually:")
        print("pip install -r requirements.txt")

def download_spacy_model():
    """Download required spaCy model"""
    print("Downloading spaCy English model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("spaCy model downloaded successfully")
    except subprocess.CalledProcessError:
        print("Error downloading spaCy model. Please download manually:")
        print("python -m spacy download en_core_web_sm")

def create_config_files():
    """Create initial configuration files"""
    # Copy example config if config.ini doesn't exist
    if not os.path.exists('config/config.ini'):
        print("Creating configuration file...")
        # The config file creation is handled by Settings class
        from config.settings import Settings
        settings = Settings()
        print("Configuration file created at config/config.ini")
        print("Please edit config/config.ini to add your API keys")

def create_test_data():
    """Create test dataset"""
    print("Creating test dataset...")
    save_test_claims_csv()
    print("Test claims saved to data/test_claims.csv")

def main():
    """Main setup function"""
    print("Setting up Automated Skeptic MVP...")
    
    create_directory_structure()
    create_test_data()
    create_config_files()
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit config/config.ini to add your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Download spaCy model: python -m spacy download en_core_web_sm")
    print("4. Run tests: pytest tests/")
    print("5. Process a claim: python main.py --claim 'The Berlin Wall fell in 1989.'")

if __name__ == "__main__":
    main()
