"""
Global configuration and environment variable handling for Strava secrets
and optional encryption.
"""

import os

CONFIG_FILE = "config.txt"

# Attempt to read password / buffer size from local config file
if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as file_handle:
        lines = file_handle.read().splitlines()
        BUFFER_SIZE = int(lines[0].strip())  # First line
        ENCRYPTION_PASSWORD = lines[1].strip()  # Second line
        CLIENT_ID = lines[2].strip()  # Third line
        CLIENT_SECRET = lines[3].strip()  # Forth line
else:
    # Fallback to environment variables
    BUFFER_SIZE = int(os.environ.get("BUFFERSIZE", 65536))  # default 64KB
    ENCRYPTION_PASSWORD = os.environ.get("ENCRYPTIONPASSWORD", "default_password")
    CLIENT_ID = os.environ.get("CLIENTID", "")
    CLIENT_SECRET = os.environ.get("CLIENTSECRET", "")


def get_buffer_size() -> int:
    """
    Returns the buffer size used for file encryption/decryption.
    Reads from config.txt if present, otherwise from environment variables.
    """
    return BUFFER_SIZE


def get_encryption_password() -> str:
    """
    Returns the encryption password used for securing the database file.
    Reads from config.txt if present, otherwise from environment variables.
    """
    return ENCRYPTION_PASSWORD


def get_client_id() -> str:
    """
    Retrieves Strava client ID from environment variables.
    """
    return CLIENT_ID


def get_client_secret() -> str:
    """
    Retrieves Strava client secret from environment variables.
    """
    return CLIENT_SECRET
