
import os
from pathlib import Path
import logging
import json
import hmac
import hashlib
from typing import Optional, Dict, List
from dotenv import dotenv_values

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring module not available - falling back to file-based storage")

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography module not available - file-based encryption disabled")

logger = logging.getLogger("OSINT_Tool")


class EnvSyncError(Exception):
    """Raised when .env file is out of sync with encrypted storage."""
    pass


class SecretsManager:
    """
    Secure credential management using OS Keyring (Priority) and Encrypted File (Fallback).
    
    Priority order for credential retrieval:
    1. Environment variables (most secure for production/CI)
    2. OS Keyring (secure local storage)
    3. Encrypted local file (fallback/legacy)
    
    SECURITY NOTE: The file-based fallback relies on OS file permissions (ACLs/chmod) to protect 
    the encryption key and salt. Physical access or root/admin access to the machine compromises this.
    """
    
    def __init__(self):
        self.service_name = "hermes-osint-tool"
        
        # Fallback storage setup
        self.secrets_dir = Path.home() / ".osint_secrets"
        self.secrets_dir.mkdir(mode=0o700, exist_ok=True)
        
        self.key_file = self.secrets_dir / ".key"
        self.creds_file = self.secrets_dir / "credentials.enc"

        self.hmac_salt = self._get_or_create_hmac_salt()
        self._cipher = None
        self._env_hash_key = "_ENV_HASH"
        
        # Check if we should migrate legacy secrets
        if KEYRING_AVAILABLE and self.creds_file.exists():
            # We don't auto-migrate on init to avoid slowing down startup, 
            # but we could log a suggestion.
            logger.debug("Legacy secrets file found. Run migration if needed.")

    def get_credential(self, key_name: str) -> Optional[str]:
        """
        Retrieve credential with priority:
        1. Environment variable
        2. OS Keyring
        3. Encrypted file (Fallback)
        """
        # Priority 1: Environment variable
        env_var = key_name.upper().replace('-', '_')
        env_value = os.getenv(env_var)
        if env_value:
            logger.debug(f"Loaded credential '{key_name}' from environment variable")
            return env_value
        
        # Priority 2: OS Keyring
        if KEYRING_AVAILABLE:
            try:
                value = keyring.get_password(self.service_name, key_name)
                if value:
                    logger.debug(f"Loaded credential '{key_name}' from OS keyring")
                    return value
            except Exception as e:
                logger.debug(f"Keyring lookup failed for '{key_name}': {e}")
        
        # Priority 3: Encrypted file (Fallback)
        value = self._read_encrypted_file(key_name)
        if value:
            logger.debug(f"Loaded credential '{key_name}' from encrypted file")
        return value
    
    def store_credential(self, key_name: str, value: str):
        """
        Store credential. Tries OS Keyring first, falls back to encrypted file.
        """
        stored_in_keyring = False
        
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(self.service_name, key_name, value)
                logger.info(f"✓ Credential '{key_name}' stored securely in OS keychain")
                stored_in_keyring = True
            except Exception as e:
                logger.warning(f"Failed to store in keyring: {e}")
        
        if not stored_in_keyring:
            if not CRYPTO_AVAILABLE:
                logger.error("Cannot store credential - cryptography module not installed and keyring failed")
                return
            
            self._write_encrypted_file(key_name, value)
            logger.info(f"✓ Credential '{key_name}' stored in encrypted fallback file")

    def migrate_legacy_secrets(self):
        """Migrate secrets from file-based storage to OS Keyring."""
        if not KEYRING_AVAILABLE:
            logger.error("Keyring not available, cannot migrate.")
            return

        if not self.creds_file.exists():
            logger.info("No legacy secrets file found.")
            return

        # SECURITY: Verify HMAC integrity before migration
        logger.info("Verifying integrity of legacy secrets before migration...")
        
        # Read file and check HMAC
        try:
            with open(self.creds_file, 'rb') as f:
                file_content = f.read()
            
            if len(file_content) < 32:
                logger.error("Legacy secrets file is corrupt (too small). Aborting migration.")
                return
            
            stored_hmac = file_content[:32]
            encrypted_data = file_content[32:]
            
            hmac_key = self._get_hmac_key()
            if not hmac_key:
                logger.error("Cannot derive HMAC key. Aborting migration for safety.")
                return
            
            calculated_hmac = hmac.new(hmac_key, encrypted_data, hashlib.sha256).digest()
            
            if not hmac.compare_digest(stored_hmac, calculated_hmac):
                logger.error("HMAC verification failed! Legacy credentials may be compromised. Aborting migration.")
                logger.warning("Please verify your credentials file manually before migration.")
                return
            
            logger.info("✓ HMAC verification passed. Credentials are intact.")
            
        except Exception as e:
            logger.error(f"Failed to verify credentials integrity: {e}. Aborting migration.")
            return

        logger.info("Migrating legacy secrets to OS Keyring...")
        credentials = self._read_all_encrypted_file()
        
        migrated_count = 0
        for key, value in credentials.items():
            if key == self._env_hash_key:
                continue # Don't migrate internal hash
                
            try:
                keyring.set_password(self.service_name, key, value)
                migrated_count += 1
                logger.debug(f"Migrated '{key}'")
            except Exception as e:
                logger.error(f"Failed to migrate '{key}': {e}")
        
        logger.info(f"✓ Successfully migrated {migrated_count} credentials to keyring.")
        
        # Optional: Rename old file to backup
        try:
            backup_path = self.creds_file.with_suffix('.enc.backup')
            self.creds_file.rename(backup_path)
            logger.info(f"Legacy credentials file backed up to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to backup legacy file: {e}")

    # --- File-Based Fallback Methods (Private) ---

    def _get_cipher(self):
        """Get or create Fernet cipher for encryption."""
        if not CRYPTO_AVAILABLE:
            return None
        
        if self._cipher:
            return self._cipher
        
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            self.key_file.touch(mode=0o600)
            
            # SECURITY: Windows-specific permission hardening
            # On Windows, chmod 0o600 doesn't work properly, so use icacls
            import platform
            if platform.system() == 'Windows':
                try:
                    import subprocess
                    # Remove all inherited permissions and grant only current user full control
                    subprocess.run([
                        'icacls', str(self.key_file), 
                        '/inheritance:r',  # Remove inheritance
                        '/grant:r', f'{os.getenv("USERNAME")}:(F)'  # Grant full control to current user only
                    ], check=True, capture_output=True)
                    logger.debug(f"Set Windows ACLs on {self.key_file}")
                except Exception as e:
                    logger.warning(f"Failed to set Windows ACLs on key file: {e}")
            
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
        self._cipher = Fernet(key)
        return self._cipher
    
    def _get_or_create_hmac_salt(self) -> bytes:
        """Get existing HMAC salt or create new one."""
        salt_file = self.secrets_dir / '.hmac_salt'
        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(32)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            return salt

    def _get_hmac_key(self):
        """Derive HMAC key from encryption key using HKDF."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        if not self.key_file.exists():
            return None

        with open(self.key_file, 'rb') as f:
            master_key = f.read()

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.hmac_salt,
            info=b'hmac-key'
        )
        return hkdf.derive(master_key)

    def _read_all_encrypted_file(self) -> Dict[str, str]:
        """Read all encrypted credentials from file with HMAC verification."""
        if not CRYPTO_AVAILABLE or not self.creds_file.exists():
            return {}
            
        try:
            cipher = self._get_cipher()
            if not cipher:
                return {}
            
            with open(self.creds_file, 'rb') as f:
                file_content = f.read()
            
            if not file_content:
                return {}

            # Try HMAC verification first
            if len(file_content) >= 32:
                stored_hmac = file_content[:32]
                encrypted_data = file_content[32:]
                
                hmac_key = self._get_hmac_key()
                if hmac_key:
                    calculated_hmac = hmac.new(hmac_key, encrypted_data, hashlib.sha256).digest()
                    if hmac.compare_digest(stored_hmac, calculated_hmac):
                        try:
                            decrypted = cipher.decrypt(encrypted_data)
                            return json.loads(decrypted.decode())
                        except Exception:
                            pass
            
            # Legacy fallback
            try:
                decrypted = cipher.decrypt(file_content)
                return json.loads(decrypted.decode())
            except Exception:
                pass
                
            return {}
            
        except Exception as e:
            logger.error(f"Failed to read credentials file: {e}")
            return {}
    
    def _read_encrypted_file(self, key_name: str) -> Optional[str]:
        credentials = self._read_all_encrypted_file()
        return credentials.get(key_name)
    
    def _write_encrypted_file(self, key_name: str, value: str):
        try:
            cipher = self._get_cipher()
            if not cipher:
                return
            
            credentials = self._read_all_encrypted_file()
            credentials[key_name] = value
            
            plaintext = json.dumps(credentials).encode()
            encrypted_data = cipher.encrypt(plaintext)
            
            hmac_key = self._get_hmac_key()
            if not hmac_key:
                return
                
            calculated_hmac = hmac.new(hmac_key, encrypted_data, hashlib.sha256).digest()
            
            self.creds_file.touch(mode=0o600)
            with open(self.creds_file, 'wb') as f:
                f.write(calculated_hmac + encrypted_data)
                
        except Exception as e:
            logger.error(f"Failed to write credential to file: {e}")

    def list_stored_credentials(self) -> List[str]:
        """List all stored credential keys (from both keyring and file)."""
        keys = set()
        
        # From file
        file_creds = self._read_all_encrypted_file()
        keys.update(file_creds.keys())
        
        # From keyring? Keyring doesn't easily support listing all keys for a service 
        # without backend-specific hacks. We'll stick to listing what we know 
        # or what we can find in the file fallback.
        # Ideally, we'd maintain a list of known keys, but for now, we return what we have.
        
        return list(keys)

    def import_from_env_file(self, env_path: str = '.env'):
        """Import values from .env file into secure storage."""
        env_values = dotenv_values(env_path)
        if not env_values:
            return

        imported_count = 0
        for key, value in env_values.items():
            if value:
                self.store_credential(key, value)
                imported_count += 1
        
        logger.info(f"✓ Imported {imported_count} values from {env_path}")
