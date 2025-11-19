import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("OSINT_Tool")


class ConfigManager:
    """
    Configuration management system with YAML-based profiles.
    Supports saving/loading scan configurations and customization.
    """
    
    DEFAULT_CONFIG = {
        'timing': {
            'min_delay': 2.0,
            'max_delay': 5.0,
            'search_delay_min': 3.0,
            'search_delay_max': 7.0,
            'timeout': 15,
            'rate_limit_backoff': 30
        },
        'platforms': {
            'social_media': {
                'twitter': True,
                'instagram': True,
                'facebook': True,
                'linkedin': True,
                'github': True,
                'pinterest': True,
                'tiktok': True
            },
            'search_engines': {
                'duckduckgo': True,
                'bing': True
            }
        },
        'features': {
            'email_enumeration': True,
            'username_variations': False,
            'domain_enumeration': False,
            'verification': True,
            'deduplication': True,
            'progress_indicators': True
        },
        'thresholds': {
            'similarity_threshold': 0.85,
            'quality_score_minimum': 0,
            'max_results_per_search': 10,
            'max_dork_queries': 9
        },
        'output': {
            'default_format': 'json',
            'verbose': True,
            'save_cache': True,
            'cache_duration_hours': 24
        },
        'api_keys': {
            'google_api_key': None,
            'google_cse_id': None,
            'twitter_bearer_token': None
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files (default: .osint_profiles)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use .osint_profiles in project root
            self.config_dir = Path.cwd() / '.osint_profiles'
        
        self.config_dir.mkdir(exist_ok=True)
        self.current_config = self.DEFAULT_CONFIG.copy()
    
    def load_config(self, profile_name: str = 'default') -> Dict[str, Any]:
        """
        Load configuration from a profile file.
        
        Args:
            profile_name: Name of the profile to load (without .yaml extension)
            
        Returns:
            Configuration dictionary
        """
        profile_path = self.config_dir / f"{profile_name}.yaml"
        
        if not profile_path.exists():
            logger.warning(f"Profile '{profile_name}' not found, using default configuration")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(profile_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Merge with default config to ensure all keys exist
            config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            
            logger.info(f"✓ Loaded configuration profile: {profile_name}")
            self.current_config = config
            return config
            
        except Exception as e:
            logger.error(f"Failed to load profile '{profile_name}': {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, profile_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Save configuration to a profile file.
        
        Args:
            profile_name: Name for the profile (without .yaml extension)
            config: Configuration dictionary (uses current_config if None)
        """
        profile_path = self.config_dir / f"{profile_name}.yaml"
        config_to_save = config or self.current_config
        
        try:
            with open(profile_path, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"✓ Saved configuration profile: {profile_name}")
            
        except Exception as e:
            logger.error(f"Failed to save profile '{profile_name}': {e}")
    
    def create_default_profile(self):
        """Create the default configuration profile if it doesn't exist."""
        default_path = self.config_dir / 'default.yaml'
        
        if not default_path.exists():
            self.save_config('default', self.DEFAULT_CONFIG)
            logger.info("Created default configuration profile")
    
    def create_quick_scan_profile(self):
        """Create a quick scan profile with minimal checks."""
        quick_config = self.DEFAULT_CONFIG.copy()
        quick_config['timing']['min_delay'] = 1.0
        quick_config['timing']['max_delay'] = 2.0
        quick_config['features']['verification'] = False
        quick_config['features']['email_enumeration'] = False
        quick_config['thresholds']['max_results_per_search'] = 5
        quick_config['thresholds']['max_dork_queries'] = 3
        
        self.save_config('quick_scan', quick_config)
        logger.info("Created quick_scan profile")
    
    def create_deep_scan_profile(self):
        """Create a deep scan profile with all features enabled."""
        deep_config = self.DEFAULT_CONFIG.copy()
        deep_config['features']['email_enumeration'] = True
        deep_config['features']['username_variations'] = True
        deep_config['features']['verification'] = True
        deep_config['thresholds']['max_results_per_search'] = 20
        deep_config['thresholds']['max_dork_queries'] = 15
        
        self.save_config('deep_scan', deep_config)
        logger.info("Created deep_scan profile")
    
    def list_profiles(self) -> list:
        """
        List all available configuration profiles.
        
        Returns:
            List of profile names (without .yaml extension)
        """
        profiles = []
        for file in self.config_dir.glob('*.yaml'):
            profiles.append(file.stem)
        return sorted(profiles)
    
    def get_platform_config(self, platform_type: str) -> Dict[str, bool]:
        """
        Get platform configuration for a specific type.
        
        Args:
            platform_type: 'social_media' or 'search_engines'
            
        Returns:
            Dictionary of platform: enabled status
        """
        return self.current_config.get('platforms', {}).get(platform_type, {})
    
    def is_platform_enabled(self, platform_type: str, platform_name: str) -> bool:
        """
        Check if a specific platform is enabled.
        
        Args:
            platform_type: 'social_media' or 'search_engines'
            platform_name: Name of the platform
            
        Returns:
            True if enabled, False otherwise
        """
        platforms = self.get_platform_config(platform_type)
        return platforms.get(platform_name.lower(), False)
    
    def get_timing_config(self) -> Dict[str, float]:
        """Get timing configuration."""
        return self.current_config.get('timing', {})
    
    def get_feature_config(self) -> Dict[str, bool]:
        """Get feature configuration."""
        return self.current_config.get('features', {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if enabled, False otherwise
        """
        features = self.get_feature_config()
        return features.get(feature_name, False)
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """
        Recursively merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result


# Convenience function
def load_config_profile(profile_name: str = 'default') -> Dict[str, Any]:
    """
    Load a configuration profile.
    
    Args:
        profile_name: Name of the profile to load
        
    Returns:
        Configuration dictionary
    """
    manager = ConfigManager()
    return manager.load_config(profile_name)
