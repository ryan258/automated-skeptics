# automated_skeptic_mvp/config/settings.py
"""
Configuration management for the Automated Skeptic MVP
"""

import configparser
import os
from typing import Dict, Any

class Settings:
    """Configuration settings manager"""
    
    def __init__(self, config_path: str = "config/config.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        self._load_config()
        self._load_environment_variables()
    
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            # Create default configuration
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        self.config['API_KEYS'] = {
            'openai_api_key': '',
            'news_api_key': '',
            'google_search_api_key': '',
            'google_search_engine_id': ''
        }
        
        self.config['API_SETTINGS'] = {
            'request_timeout': '30',
            'max_retries': '3',
            'rate_limit_delay': '1.0'
        }
        
        self.config['PROCESSING'] = {
            'max_sources_per_claim': '5',
            'confidence_threshold': '0.7',
            'cache_expiry_hours': '24'
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            self.config.write(f)
    
    def _load_environment_variables(self):
        """Override config with environment variables if available"""
        env_mappings = {
            'OPENAI_API_KEY': ('API_KEYS', 'openai_api_key'),
            'NEWS_API_KEY': ('API_KEYS', 'news_api_key'),
            'GOOGLE_SEARCH_API_KEY': ('API_KEYS', 'google_search_api_key'),
            'GOOGLE_SEARCH_ENGINE_ID': ('API_KEYS', 'google_search_engine_id')
        }
        
        for env_var, (section, key) in env_mappings.items():
            if env_var in os.environ:
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = os.environ[env_var]
    
    def get(self, section: str, key: str, fallback: str = '') -> str:
        """Get configuration value"""
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        return self.config.getfloat(section, key, fallback=fallback)