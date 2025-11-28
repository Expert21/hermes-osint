from src.core.config_manager import ConfigManager
from src.core.secrets_manager import SecretsManager, EnvSyncError
import sys

def verify():
    print("Verifying configuration...")
    
    # Check sync first (mimic main.py)
    secrets = SecretsManager()
    try:
        secrets.validate_env_sync()
        print("Sync check passed.")
    except EnvSyncError as e:
        print(f"Sync check failed: {e}")
        return

    cm = ConfigManager()
    config = cm.load_config()
    
    min_delay = config['timing']['min_delay']
    print(f"TIMING_MIN_DELAY: {min_delay}")
    print(f"Type: {type(min_delay)}")
    
    if min_delay == 99.9 and isinstance(min_delay, float):
        print("SUCCESS: Config loaded correctly.")
    else:
        print("FAILURE: Config value mismatch.")

if __name__ == "__main__":
    verify()
