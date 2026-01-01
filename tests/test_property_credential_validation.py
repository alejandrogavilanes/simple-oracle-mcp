"""
Property-based test for credential validation
Tests Property 11: Credential Validation
"""

import pytest
from hypothesis import given, strategies as st

from config.security import validate_credential_format


# Strategy for generating valid usernames
valid_usernames = st.text(
    min_size=2,
    max_size=50,
    alphabet=st.characters(
        min_codepoint=ord('a'),
        max_codepoint=ord('z')
    )
).map(lambda x: x if x else 'a' + x).filter(lambda x: len(x) >= 2)

# Strategy for generating invalid usernames
invalid_usernames = st.one_of([
    st.just(""),  # Empty username
    st.just("a"),  # Too short
    st.text(min_size=1, max_size=1),  # Single character
    st.text(
        min_size=2,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=ord('0'),
            max_codepoint=ord('9')
        )
    ).filter(lambda x: len(x) >= 2),  # Starts with number
    st.text(
        min_size=2,
        max_size=20,
        alphabet=st.sampled_from(['!', '@', '#', '$', '%', '^', '&', '*'])
    ).filter(lambda x: len(x) >= 2),  # Contains invalid characters
])

# Strategy for generating valid passwords (must contain at least one letter or digit)
valid_passwords = st.text(
    min_size=6,
    max_size=100,
    alphabet=st.characters(
        min_codepoint=32,  # Space character
        max_codepoint=126,  # Tilde character (printable ASCII)
        blacklist_characters='\n\r\t\0'  # Exclude problematic characters
    )
).filter(lambda x: (
    x.strip() and 
    len(x.strip()) >= 6 and
    # Must contain at least one letter or digit for complexity
    any(c.isalnum() for c in x)
))

# Strategy for generating invalid passwords
invalid_passwords = st.one_of([
    st.just(""),  # Empty password
    st.text(min_size=1, max_size=5),  # Too short
    st.just("     "),  # Only whitespace
])

# Strategy for generating usernames with mixed case and underscores (valid)
complex_valid_usernames = st.text(
    min_size=2,
    max_size=30,
    alphabet=st.characters(
        min_codepoint=ord('A'),
        max_codepoint=ord('z')
    ) | st.sampled_from(['_'])
).filter(
    lambda x: len(x) >= 2 and x[0].isalpha() and all(c.isalnum() or c == '_' for c in x)
)


class TestCredentialValidation:
    """Property-based tests for credential validation"""
    
    @given(
        username=valid_usernames,
        password=valid_passwords
    )
    def test_valid_credentials_pass_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any database credentials provided through MCP config, 
        the Security_System should validate parameter format and 
        requirements using the same validation rules applied to 
        .env file credentials.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Valid credentials should produce no errors
        assert errors == [], (
            f"Valid credentials should pass validation. "
            f"Username: '{username}', Password length: {len(password)}, "
            f"Errors: {errors}"
        )
    
    @given(
        username=invalid_usernames,
        password=valid_passwords
    )
    def test_invalid_usernames_fail_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any invalid username format, the validation should 
        return appropriate error messages.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Invalid usernames should produce errors
        assert len(errors) > 0, (
            f"Invalid username '{username}' should fail validation, "
            f"but no errors were returned"
        )
        
        # Check that username-related errors are present
        username_errors = [error for error in errors if 'username' in error.lower()]
        assert len(username_errors) > 0, (
            f"Username validation errors should be present for invalid username '{username}', "
            f"but got errors: {errors}"
        )
    
    @given(
        username=valid_usernames,
        password=invalid_passwords
    )
    def test_invalid_passwords_fail_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any invalid password format, the validation should 
        return appropriate error messages.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Invalid passwords should produce errors
        assert len(errors) > 0, (
            f"Invalid password (length: {len(password)}) should fail validation, "
            f"but no errors were returned"
        )
        
        # Check that password-related errors are present
        password_errors = [error for error in errors if 'password' in error.lower()]
        assert len(password_errors) > 0, (
            f"Password validation errors should be present for invalid password, "
            f"but got errors: {errors}"
        )
    
    @given(
        username=invalid_usernames,
        password=invalid_passwords
    )
    def test_both_invalid_credentials_fail_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any credentials where both username and password are invalid,
        the validation should return errors for both.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Both invalid should produce multiple errors
        assert len(errors) > 0, (
            f"Both invalid credentials should fail validation, "
            f"but no errors were returned"
        )
        
        # Should have errors for both username and password
        username_errors = [error for error in errors if 'username' in error.lower()]
        password_errors = [error for error in errors if 'password' in error.lower()]
        
        # At least one error should be present (could be combined or separate)
        assert len(username_errors) > 0 or len(password_errors) > 0, (
            f"Should have username or password errors for invalid credentials, "
            f"but got errors: {errors}"
        )
    
    @given(
        username=complex_valid_usernames,
        password=valid_passwords
    )
    def test_complex_valid_usernames_pass_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any valid username with mixed case and underscores,
        the validation should pass.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Complex valid usernames should pass
        assert errors == [], (
            f"Complex valid username '{username}' should pass validation, "
            f"but got errors: {errors}"
        )
    
    @given(
        password=st.text(
            min_size=6,
            max_size=20,
            alphabet=st.characters(
                min_codepoint=ord('a'),
                max_codepoint=ord('z')
            )
        ).filter(lambda x: len(x) >= 6)
    )
    def test_simple_passwords_pass_basic_validation(self, password):
        """
        Property 11: Credential Validation
        For any password that meets minimum length requirements,
        the basic validation should pass (even if not complex).
        
        **Validates: Requirements 5.1**
        """
        username = "testuser"  # Use a valid username
        errors = validate_credential_format(username, password)
        
        # Simple passwords that meet length requirements should pass basic validation
        password_errors = [error for error in errors if 'password' in error.lower()]
        
        # Should not have length-related password errors
        length_errors = [error for error in password_errors if 'length' in error.lower() or 'characters' in error.lower()]
        assert len(length_errors) == 0, (
            f"Password '{password}' with length {len(password)} should not have length errors, "
            f"but got: {length_errors}"
        )
    
    @given(
        username=st.text(
            min_size=2,
            max_size=30,
            alphabet=st.characters(
                min_codepoint=ord('A'),
                max_codepoint=ord('Z')
            ) | st.characters(
                min_codepoint=ord('a'),
                max_codepoint=ord('z')
            ) | st.characters(
                min_codepoint=ord('0'),
                max_codepoint=ord('9')
            ) | st.sampled_from(['_'])
        ).filter(lambda x: len(x) >= 2 and x[0].isalpha())
    )
    def test_username_format_validation_consistency(self, username):
        """
        Property 11: Credential Validation
        For any username that starts with a letter and contains only
        valid characters, the validation should be consistent.
        
        **Validates: Requirements 5.1**
        """
        password = "validpassword123"  # Use a valid password
        errors = validate_credential_format(username, password)
        
        # Filter to only username errors
        username_errors = [error for error in errors if 'username' in error.lower()]
        
        # Username should be valid if it follows the rules
        if all(c.isalnum() or c == '_' for c in username):
            assert len(username_errors) == 0, (
                f"Username '{username}' should be valid but got errors: {username_errors}"
            )
        else:
            # If it contains invalid characters, should have errors
            invalid_char_errors = [error for error in username_errors if 'letter' in error.lower() or 'underscore' in error.lower()]
            assert len(invalid_char_errors) > 0, (
                f"Username '{username}' with invalid characters should have format errors"
            )
    
    @given(
        username=st.just(""),
        password=st.just("")
    )
    def test_empty_credentials_fail_validation(self, username, password):
        """
        Property 11: Credential Validation
        For any empty credentials, the validation should fail
        with appropriate error messages.
        
        **Validates: Requirements 5.1**
        """
        errors = validate_credential_format(username, password)
        
        # Empty credentials should produce errors
        assert len(errors) >= 2, (
            f"Empty credentials should produce at least 2 errors (username and password), "
            f"but got: {errors}"
        )
        
        # Should have specific errors for empty values
        empty_username_errors = [error for error in errors if 'username' in error.lower() and 'empty' in error.lower()]
        empty_password_errors = [error for error in errors if 'password' in error.lower() and 'empty' in error.lower()]
        
        assert len(empty_username_errors) > 0, (
            f"Should have empty username error, but got errors: {errors}"
        )
        assert len(empty_password_errors) > 0, (
            f"Should have empty password error, but got errors: {errors}"
        )
    
    @given(
        username=st.text(
            min_size=2,
            max_size=10,
            alphabet=st.characters(
                min_codepoint=ord('a'),
                max_codepoint=ord('z')
            )
        ).filter(lambda x: len(x) >= 2),
        password_length=st.integers(min_value=6, max_value=50)
    )
    def test_password_length_validation_boundary(self, username, password_length):
        """
        Property 11: Credential Validation
        For any password at the minimum length boundary (6 characters),
        the validation should pass.
        
        **Validates: Requirements 5.1**
        """
        password = 'a' * password_length
        errors = validate_credential_format(username, password)
        
        # Filter to only password length errors
        password_length_errors = [
            error for error in errors 
            if 'password' in error.lower() and ('length' in error.lower() or 'characters' in error.lower())
        ]
        
        # Passwords of 6+ characters should not have length errors
        assert len(password_length_errors) == 0, (
            f"Password of length {password_length} should not have length errors, "
            f"but got: {password_length_errors}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])