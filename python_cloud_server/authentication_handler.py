"""Authentication handler for the server."""

import hashlib
import logging
import os
import secrets

from dotenv import load_dotenv, set_key

from python_cloud_server.config import ROOT_DIR

logger = logging.getLogger(__name__)

ENV_FILE = ROOT_DIR / ".env"
ENV_VAR_NAME = "API_TOKEN_HASH"
TOKEN_LENGTH = 32


def generate_token() -> str:
    """Generate a secure random token.

    :return str: A URL-safe token string
    """
    return secrets.token_urlsafe(TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """Hash a token string using SHA-256.

    :param str token: The plain text token to hash
    :return str: The hexadecimal representation of the hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def save_hashed_token(token: str) -> None:
    """Hash a token and save it to the .env file.

    :param str token: The plain text token to hash and save
    """
    hashed = hash_token(token)

    if not ENV_FILE.exists():
        ENV_FILE.touch()

    set_key(ENV_FILE, ENV_VAR_NAME, hashed)


def load_hashed_token() -> str | None:
    """Load the hashed token from the .env file.

    :return str | None: The hashed token string, or None if not found
    """
    load_dotenv(ENV_FILE)
    return os.getenv(ENV_VAR_NAME)


def verify_token(token: str) -> bool:
    """Verify a token against the stored hash.

    :param str token: The plain text token to verify
    :return bool: True if the token matches the stored hash, False otherwise
    """
    if (stored_hash := load_hashed_token()) is None:
        msg = "No stored token hash found for verification."
        raise ValueError(msg)

    return hash_token(token) == stored_hash


def generate_new_token() -> None:
    """Generate a new token, hash it, and save the hash to the .env file.

    This function generates a new secure random token, hashes it using SHA-256,
    and saves the hashed token to the .env file for future verification.
    """
    new_token = generate_token()
    save_hashed_token(new_token)
    logger.info("New API token generated and saved. Token: %s", new_token)
