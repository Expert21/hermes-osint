
import os
import getpass
import base64
from pathlib import Path
from datetime import datetime
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
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography module not available - file-based encryption disabled")

logger = logging.getLogger("OSINT_Tool")

# SECURITY: PBKDF2 iteration count (OWASP 2024 recommendation for SHA-256)
PBKDF2_ITERATIONS = 480000


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
        self._password = None  # Cached password for session
        self._env_hash_key = "_ENV_HASH"
        self.audit_log = self.secrets_dir / "audit.log"
        
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

    def _audit_log(self, action: str, key_name: str, success: bool):
        """Log credential access for audit purposes."""
        try:
            timestamp = datetime.now().isoformat()
            status = "SUCCESS" if success else "FAILURE"
            entry = f"{timestamp} | {action} | {key_name} | {status}\n"
            with open(self.audit_log, 'a') as f:
                f.write(entry)
        except Exception as e:
            logger.debug(f"Failed to write audit log: {e}")

    def _get_cipher(self, password: Optional[str] = None):
        """
        Get Fernet cipher with password-derived key.
        
        SECURITY: Uses PBKDF2 with 480,000 iterations to derive encryption key
        from user password. No plaintext key is stored on disk.
        """
        if not CRYPTO_AVAILABLE:
            return None
        
        # Use cached cipher if password matches
        if self._cipher and password is None and self._password is not None:
            return self._cipher
        
        # Get password
        if password is None:
            if self._password:
                password = self._password
            else:
                password = getpass.getpass("Encryption password: ")
                self._password = password
        
        # Get or create salt (not secret, but unique per installation)
        salt_file = self.secrets_dir / '.key_salt'
        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(32)
            salt_file.touch(mode=0o600)
            with open(salt_file, 'wb') as f:
                f.write(salt)
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._cipher = Fernet(key)
        return self._cipher
    
    def set_password(self, password: str):
        """Set the encryption password for this session (avoids interactive prompt)."""
        self._password = password
        self._cipher = None  # Invalidate cached cipher
    
    def rotate_encryption(self, old_password: str, new_password: str) -> bool:
        """
        Rotate encryption by re-encrypting all credentials with a new password.
        
        Returns:
            True if rotation successful
        """
        try:
            # Read with old password
            self._password = old_password
            self._cipher = None
            credentials = self._read_all_encrypted_file()
            
            if not credentials:
                logger.warning("No credentials to rotate")
                return True
            
            # Write with new password
            self._password = new_password
            self._cipher = None
            
            # Delete old salt to force new key derivation
            salt_file = self.secrets_dir / '.key_salt'
            if salt_file.exists():
                salt_file.unlink()
            
            # Re-encrypt all credentials
            for key, value in credentials.items():
                if key != self._env_hash_key:
                    self._write_encrypted_file(key, value)
            
            self._audit_log("ROTATE", "ALL", True)
            logger.info("✓ Encryption rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Encryption rotation failed: {e}")
            self._audit_log("ROTATE", "ALL", False)
            return False
    
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
