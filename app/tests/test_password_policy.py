"""Tests for PasswordPolicy - validation, complexity, history."""
import pytest

from services.password_policy import PasswordPolicy
from storage.database import Database
import app_config


class TestPasswordValidation:
    """Test password complexity validation."""
    
    def test_valid_password(self, password_policy):
        """Test a password that meets all requirements."""
        is_valid, message = password_policy.validate("SecurePass@123")
        
        assert is_valid is True
        assert message == []  # Empty list when valid
    
    def test_password_too_short(self, password_policy):
        """Test password shorter than minimum length."""
        is_valid, message = password_policy.validate("Short1!")
        
        assert is_valid is False
        assert any("at least" in msg.lower() or "characters" in msg.lower() for msg in message)
    
    def test_password_no_uppercase(self, password_policy):
        """Test password without uppercase letter."""
        is_valid, message = password_policy.validate("lowercase123!")
        
        assert is_valid is False
        assert any("uppercase" in msg.lower() for msg in message)
    
    def test_password_no_lowercase(self, password_policy):
        """Test password without lowercase letter."""
        is_valid, message = password_policy.validate("UPPERCASE123!")
        
        assert is_valid is False
        assert any("lowercase" in msg.lower() for msg in message)
    
    def test_password_no_digit(self, password_policy):
        """Test password without digit."""
        is_valid, message = password_policy.validate("NoDigitsHere!")
        
        assert is_valid is False
        assert any("digit" in msg.lower() or "number" in msg.lower() for msg in message)
    
    def test_password_no_special_char(self, password_policy):
        """Test password without special character."""
        is_valid, message = password_policy.validate("NoSpecialChar123")
        
        assert is_valid is False
        assert any("special" in msg.lower() for msg in message)
    
    def test_password_exactly_minimum_length(self, password_policy):
        """Test password at exactly minimum length."""
        # Create password with exactly PASSWORD_MIN_LENGTH characters
        min_length = app_config.PASSWORD_MIN_LENGTH
        password = "A" * (min_length - 3) + "a1!"  # Meets all requirements
        
        is_valid, message = password_policy.validate(password)
        assert is_valid is True
    
    def test_password_with_multiple_special_chars(self, password_policy):
        """Test password with multiple special characters."""
        is_valid, message = password_policy.validate("P@ssw0rd!#$")
        
        assert is_valid is True
    
    def test_empty_password(self, password_policy):
        """Test empty password."""
        is_valid, message = password_policy.validate("")
        
        assert is_valid is False
    
    def test_password_with_spaces(self, password_policy):
        """Test password with spaces (should be allowed)."""
        is_valid, message = password_policy.validate("Pass Word@123")
        
        assert is_valid is True


# TestPasswordHistory class removed - password history methods belong to PasswordHistoryManager, not PasswordPolicy
# Password history is managed separately and integrated through UserService


class TestPasswordPolicyConfiguration:
    """Test password policy configuration from environment."""
    
    def test_minimum_length_from_config(self, password_policy):
        """Test minimum length uses configuration value."""
        # Create password one character shorter than minimum
        # If PASSWORD_MIN_LENGTH is 8, we need 7 characters total
        if app_config.PASSWORD_MIN_LENGTH > 3:
            short_password = "A" * (app_config.PASSWORD_MIN_LENGTH - 4) + "a1!"
        else:
            short_password = "a1!"
        
        is_valid, message = password_policy.validate(short_password)
        assert is_valid is False, f"Password '{short_password}' should be invalid (too short)"
        
        # Password at minimum length should be valid
        valid_password = "A" * (app_config.PASSWORD_MIN_LENGTH - 3) + "a1!"
        is_valid, message = password_policy.validate(valid_password)
        assert is_valid is True, f"Password '{valid_password}' should be valid (at minimum length)"
    
    # test_history_count_from_config removed - uses PasswordHistoryManager methods


class TestPasswordComplexityEdgeCases:
    """Test edge cases in password validation."""
    
    def test_password_with_unicode_characters(self, password_policy):
        """Test password with unicode characters."""
        is_valid, message = password_policy.validate("Pässw0rd!123")
        
        # Should be valid (unicode counts as special characters)
        assert is_valid is True
    
    def test_password_with_only_numbers(self, password_policy):
        """Test password with only numbers."""
        is_valid, message = password_policy.validate("12345678")
        
        assert is_valid is False
    
    def test_password_with_only_special_chars(self, password_policy):
        """Test password with only special characters."""
        is_valid, message = password_policy.validate("!@#$%^&*()")
        
        assert is_valid is False
    
    def test_very_long_password(self, password_policy):
        """Test very long password."""
        long_password = "A" * 100 + "a1!"
        
        is_valid, message = password_policy.validate(long_password)
        assert is_valid is True
    
    def test_password_starts_with_special_char(self, password_policy):
        """Test password that starts with special character."""
        is_valid, message = password_policy.validate("!Password123")
        
        assert is_valid is True
    
    def test_password_ends_with_number(self, password_policy):
        """Test password that ends with number."""
        is_valid, message = password_policy.validate("Password!123")
        
        assert is_valid is True


# TestPasswordHashComparison class removed - uses PasswordHistoryManager methods
# Password hash comparison is handled by PasswordHistoryManager, not PasswordPolicy


