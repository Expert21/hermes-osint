<<<<<<< HEAD
try:
    import keyring
    print('keyring IS installed')
    print('Backend:', keyring.get_keyring())
    
    # Try to get a stored credential
    val = keyring.get_password('hermes-osint-tool', 'PROXY_PROVIDER')
    print('PROXY_PROVIDER from keyring:', val)
except ImportError:
    print('keyring NOT installed')
except Exception as e:
    print(f'Error: {e}')
=======
try:
    import keyring
    print('keyring IS installed')
    print('Backend:', keyring.get_keyring())
    
    # Try to get a stored credential
    val = keyring.get_password('hermes-osint-tool', 'PROXY_PROVIDER')
    print('PROXY_PROVIDER from keyring:', val)
except ImportError:
    print('keyring NOT installed')
except Exception as e:
    print(f'Error: {e}')
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
