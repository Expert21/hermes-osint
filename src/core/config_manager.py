import yaml
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path
import os
from src.core.secrets_manager import SecretsManager

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
            'twitter_bearer_token': None,
            'hibp_api_key': None,
            'facebook_access_token': None,
            'instagram_access_token': None,
            'github_access_token': None,
            'linkedin_access_token': None,
            'shodan_api_key': None,
            'censys_api_id': None,
            'censys_api_secret': None,
            'virustotal_api_key': None,
            'hunter_io_api_key': None,
            'intelx_api_key': None,
            'bing_api_key': None,
            'brave_api_key': None,
            'reddit_client_id': None,
            'reddit_client_secret': None,
            'builtwith_api_key': None,
            'urlscan_api_key': None
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
        Load configuration from a profile file with security validation.
        
        Args:
            profile_name: Name of the profile to load (without .yaml extension)
            
        Returns:
            Configuration dictionary
        """
        # Validate profile name - prevent path traversal
        if not re.match(r'^[a-zA-Z0-9_-]+$', profile_name):
            logger.error(f"Invalid profile name '{profile_name}': only alphanumeric, dash, underscore allowed")
            return self.DEFAULT_CONFIG.copy()
        
        if '..' in profile_name or '/' in profile_name or '\\' in profile_name:
            logger.error(f"Invalid profile name '{profile_name}': path traversal detected")
            return self.DEFAULT_CONFIG.copy()
        
        profile_path = self.config_dir / f"{profile_name}.yaml"
        
        # Ensure path is within config directory
        try:
            resolved_path = profile_path.resolve()
            resolved_config_dir = self.config_dir.resolve()
            
            if not str(resolved_path).startswith(str(resolved_config_dir)):
                logger.error(f"Profile path outside allowed directory: {resolved_path}")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            return self.DEFAULT_CONFIG.copy()
        
        if not profile_path.exists():
            logger.warning(f"Profile '{profile_name}' not found, using default configuration")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(profile_path, 'r') as f:
                # Use SafeLoader explicitly
                loaded_config = yaml.load(f, Loader=yaml.SafeLoader)
            
            # Validate config is a dictionary
            if not isinstance(loaded_config, dict):
                logger.error("Config must be a dictionary")
                return self.DEFAULT_CONFIG.copy()
            
            # Validate all values are safe types
            self._validate_config_types(loaded_config)
            
            # Merge with default config to ensure all keys exist
            config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            
            # Apply overrides from secrets/env
            self._apply_env_overrides(config)
            
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
    
    def _validate_config_types(self, config: dict, path: str = "") -> None:
        """
        Recursively validate config contains only safe types.
        
        Args:
            config: Configuration dictionary to validate
            path: Current path in config (for error messages)
            
        Raises:
            ValueError: If unsafe type found
        """
        safe_types = (str, int, float, bool, type(None), dict, list)
        
        for key, value in config.items():
            current_path = f"{path}.{key}" if path else key
            
            if not isinstance(value, safe_types):
                raise ValueError(f"Unsafe type {type(value).__name__} at {current_path}")
            
            if isinstance(value, dict):
                self._validate_config_types(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if not isinstance(item, safe_types):
                        raise ValueError(f"Unsafe type in list at {current_path}[{i}]")
    
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

    def _apply_env_overrides(self, config: Dict[str, Any]):
        """
        Apply overrides from SecretsManager (encrypted .env values) and actual environment variables.
        """
        secrets = SecretsManager()
        
        # 1. Get all stored credentials (which now include imported .env values)
        stored_creds = secrets._read_all_encrypted()
        
        # 2. Get actual environment variables
        env_vars = os.environ
        
        # Helper to flatten config for mapping, keeping track of the path
        def flatten_config_with_path(cfg, parent_path=None, parent_key='', sep='_'):
            items = []
            if parent_path is None:
                parent_path = []
                
            for k, v in cfg.items():
                current_path = parent_path + [k]
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                
                if isinstance(v, dict):
                    items.extend(flatten_config_with_path(v, current_path, new_key, sep=sep).items())
                else:
                    items.append((new_key.upper(), (current_path, v)))
            return dict(items)

        # Helper to set nested value using known path
        def set_nested(cfg, keys, value):
            for key in keys[:-1]:
                cfg = cfg.setdefault(key, {})
            cfg[keys[-1]] = value

        # Flatten default config to know what keys exist, their types, and their paths
        flat_defaults = flatten_config_with_path(self.DEFAULT_CONFIG)
        
        # Combine sources: Stored Secrets < Environment Variables
        for flat_key, (key_path, default_val) in flat_defaults.items():
            value_to_use = None
            
            # Check secrets/stored .env values
            if flat_key in stored_creds:
                value_to_use = stored_creds[flat_key]
                
            # Check actual environment variables (higher priority)
            if flat_key in env_vars:
                value_to_use = env_vars[flat_key]
            
            if value_to_use is not None:
                # Type conversion
                try:
                    target_type = type(default_val)
                    if target_type == bool:
                        # Handle boolean strings
                        if str(value_to_use).lower() in ('true', '1', 'yes', 'on'):
                            converted_val = True
                        elif str(value_to_use).lower() in ('false', '0', 'no', 'off'):
                            converted_val = False
                        else:
                            converted_val = bool(value_to_use)
                    elif target_type == type(None):
                        # If default is None, try to infer or keep as string
                        converted_val = value_to_use
                    else:
                        converted_val = target_type(value_to_use)
                    
                    # Set the value in the config dict using the preserved path
                    set_nested(config, key_path, converted_val)
                    logger.debug(f"Applied override for {flat_key}")
                    
                except Exception as e:
                    logger.warning(f"Failed to convert override for {flat_key}: {e}")

    def generate_env_template(self, path: str = '.env'):
        """
        Generate a .env template file with all configuration options.
        """
        template_lines = [
            "# OSINT Tool Configuration Template",
            "# Generated by --init-env",
            "#",
            "# Instructions:",
            "# 1. Uncomment lines to override default values",
            "# 2. Add your API keys",
            "# 3. Run 'python main.py --import-env' to secure these settings",
            "",
            "# --- API Keys ---",
            "# --- API Keys ---",
            "GOOGLE_API_KEY=",
            "GOOGLE_CSE_ID=",
            "TWITTER_BEARER_TOKEN=",
            "HIBP_API_KEY=",
            "FACEBOOK_ACCESS_TOKEN=",
            "INSTAGRAM_ACCESS_TOKEN=",
            "GITHUB_ACCESS_TOKEN=",
            "LINKEDIN_ACCESS_TOKEN=",
            "SHODAN_API_KEY=",
            "CENSYS_API_ID=",
            "CENSYS_API_SECRET=",
            "VIRUSTOTAL_API_KEY=",
            "HUNTER_IO_API_KEY=",
            "INTELX_API_KEY=",
            "BING_API_KEY=",
            "BRAVE_API_KEY=",
            "REDDIT_CLIENT_ID=",
            "REDDIT_CLIENT_SECRET=",
            "BUILTWITH_API_KEY=",
            "URLSCAN_API_KEY=",
            "",
            "# --- Configuration Options ---"
        ]
        
        def flatten_for_template(cfg, parent_key=''):
            items = []
            for k, v in cfg.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    if k != 'api_keys': # Skip api_keys as they are handled separately
                        items.extend(flatten_for_template(v, new_key))
                else:
                    items.append((new_key.upper(), v))
            return items

        flat_config = flatten_for_template(self.DEFAULT_CONFIG)
        
        for key, value in flat_config:
            template_lines.append(f"# {key}={value}")
            
        try:
            with open(path, 'w') as f:
                f.write('\n'.join(template_lines))
            logger.info(f"✓ Generated .env template at {path}")
        except Exception as e:
            logger.error(f"Failed to generate .env template: {e}")


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
