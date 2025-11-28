from src.core.secrets_manager import SecretsManager

sm = SecretsManager()
creds = sm._read_all_encrypted_file()

print("All stored credentials:")
for k in sorted(creds.keys()):
    val = str(creds[k])
    if len(val) > 30:
        val = val[:30] + "..."
    print(f"  {k}: {val}")
