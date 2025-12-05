
from src.core.secrets_manager import SecretsManager

def load_config():
    """
    Load configuration with secure credential handling.
    Credentials are loaded from:
    1. Environment variables (priority)
    2. Encrypted local file
    """
    secrets = SecretsManager()
    
    config = {
        "GOOGLE_API_KEY": secrets.get_credential("google_api_key"),
        "GOOGLE_CSE_ID": secrets.get_credential("google_cse_id"),
        "TWITTER_BEARER_TOKEN": secrets.get_credential("twitter_bearer_token"),
        "HIBP_API_KEY": secrets.get_credential("hibp_api_key"),
        "FACEBOOK_ACCESS_TOKEN": secrets.get_credential("facebook_access_token"),
        "INSTAGRAM_ACCESS_TOKEN": secrets.get_credential("instagram_access_token"),
        "GITHUB_ACCESS_TOKEN": secrets.get_credential("github_access_token"),
        "LINKEDIN_ACCESS_TOKEN": secrets.get_credential("linkedin_access_token"),
        "SHODAN_API_KEY": secrets.get_credential("shodan_api_key"),
        "CENSYS_API_ID": secrets.get_credential("censys_api_id"),
        "CENSYS_API_SECRET": secrets.get_credential("censys_api_secret"),
        "VIRUSTOTAL_API_KEY": secrets.get_credential("virustotal_api_key"),
        "HUNTER_IO_API_KEY": secrets.get_credential("hunter_io_api_key"),
        "INTELX_API_KEY": secrets.get_credential("intelx_api_key"),
        "BING_API_KEY": secrets.get_credential("bing_api_key"),
        "BRAVE_API_KEY": secrets.get_credential("brave_api_key"),
        "REDDIT_CLIENT_ID": secrets.get_credential("reddit_client_id"),
        "REDDIT_CLIENT_SECRET": secrets.get_credential("reddit_client_secret"),
        "BUILTWITH_API_KEY": secrets.get_credential("builtwith_api_key"),
        "URLSCAN_API_KEY": secrets.get_credential("urlscan_api_key"),
    }
    
    return config
