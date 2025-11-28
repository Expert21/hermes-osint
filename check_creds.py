<<<<<<< HEAD
from src.core.secrets_manager import SecretsManager

sm = SecretsManager()
creds = sm._read_all_encrypted_file()

print("All stored credentials:")
for k in sorted(creds.keys()):
    val = str(creds[k])
    if len(val) > 30:
        val = val[:30] + "..."
    print(f"  {k}: {val}")
=======
from src.core.secrets_manager import SecretsManager

sm = SecretsManager()
creds = sm._read_all_encrypted_file()

print("All stored credentials:")
for k in sorted(creds.keys()):
    val = str(creds[k])
    if len(val) > 30:
        val = val[:30] + "..."
    print(f"  {k}: {val}")
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
