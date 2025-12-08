# ============================================
# BotFactory AI - Security Utils Tests
# ============================================

import pytest
from datetime import datetime, timedelta

from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_password_hash_is_different(self):
        """Test that hashed password is different from plain text."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash is long

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hash(self):
        """Test that same password produces different hashes."""
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt uses random salt, so hashes should be different
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWT:
    """Tests for JWT utilities."""

    def test_create_access_token(self):
        """Test creating access token."""
        token = create_access_token("user123")
        
        assert token is not None
        assert len(token) > 50

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        token = create_refresh_token("user123")
        
        assert token is not None
        assert len(token) > 50

    def test_decode_access_token(self):
        """Test decoding access token."""
        user_id = "user123"
        token = create_access_token(user_id)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "access"

    def test_decode_refresh_token(self):
        """Test decoding refresh token."""
        user_id = "user123"
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "refresh"

    def test_verify_token_correct_type(self):
        """Test verifying token with correct type."""
        user_id = "user123"
        access_token = create_access_token(user_id)
        
        result = verify_token(access_token, token_type="access")
        assert result == user_id

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type."""
        user_id = "user123"
        access_token = create_access_token(user_id)
        
        result = verify_token(access_token, token_type="refresh")
        assert result is None

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_token("invalid_token")
        
        assert payload is None
