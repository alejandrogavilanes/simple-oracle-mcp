"""
Property-based test for credential masking in logs
Tests Property 12: Credential Masking in Logs
"""

import pytest
from hypothesis import given, strategies as st

from config.security import SecureConfigLogger


# Strategy for generating sensitive parameter names
sensitive_keys = st.sampled_from([
    "password", "PASSWORD", "Password",
    "secret", "SECRET", "Secret", 
    "key", "KEY", "Key",
    "token", "TOKEN", "Token",
    "credential", "CREDENTIAL", "Credential",
    "auth", "AUTH", "Auth",
    "pass", "PASS", "Pass",
    "oracle_password", "ORACLE_PASSWORD",
    "db_secret", "DB_SECRET",
    "api_key", "API_KEY",
    "auth_token", "AUTH_TOKEN"
])

# Strategy for generating non-sensitive parameter names
non_sensitive_keys = st.sampled_from([
    "host", "HOST", "Host",
    "port", "PORT", "Port",
    "service_name", "SERVICE_NAME",
    "username", "USERNAME", "Username",
    "timeout", "TIMEOUT", "Timeout",
    "max_rows", "MAX_ROWS",
    "connection_timeout", "CONNECTION_TIMEOUT",
    "query_timeout", "QUERY_TIMEOUT"
])

# Strategy for generating credential values
credential_values = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(
        min_codepoint=32,  # Space character
        max_codepoint=126,  # Tilde character (printable ASCII)
        blacklist_characters='\n\r\t\0'  # Exclude problematic characters
    )
).filter(lambda x: x.strip())

# Strategy for generating short credential values (≤4 characters)
short_credential_values = st.text(
    min_size=1,
    max_size=4,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip())

# Strategy for generating long credential values (>4 characters)
long_credential_values = st.text(
    min_size=5,
    max_size=100,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip())


class TestCredentialMasking:
    """Property-based tests for credential masking in logs"""
    
    @given(
        key=sensitive_keys,
        value=credential_values
    )
    def test_sensitive_parameters_are_masked(self, key, value):
        """
        Property 12: Credential Masking in Logs
        For any sensitive configuration parameter that is logged, 
        the Security_System should mask the credential value in all 
        log outputs, showing only non-sensitive portions.
        
        **Validates: Requirements 5.2**
        """
        masked_value = SecureConfigLogger.mask_sensitive_value(key, value)
        
        # Sensitive parameters should always be masked
        if len(value) <= 4:
            # Short values should be completely masked
            assert masked_value == "*" * len(value), (
                f"Short sensitive value '{value}' should be completely masked, "
                f"but got '{masked_value}'"
            )
        else:
            # Long values should show first 2 and last 2 characters
            expected_masked = value[:2] + "*" * (len(value) - 4) + value[-2:]
            assert masked_value == expected_masked, (
                f"Long sensitive value '{value}' should be masked as '{expected_masked}', "
                f"but got '{masked_value}'"
            )
        
        # Masked value should not be the same as original (unless it's already properly masked)
        if len(value) > 4 and not all(c == '*' for c in value):
            # For longer values, check if the middle section is properly masked
            expected_pattern = value[:2] + "*" * (len(value) - 4) + value[-2:]
            assert masked_value == expected_pattern, (
                f"Sensitive parameter '{key}' with value '{value}' should be masked as '{expected_pattern}', "
                f"but got '{masked_value}'"
            )
            
            # The middle section should contain asterisks (unless original was already masked)
            middle_section = masked_value[2:-2] if len(masked_value) > 4 else masked_value
            if len(middle_section) > 0:
                # If the original middle section was not all asterisks, the masked version should be
                original_middle = value[2:-2] if len(value) > 4 else value
                if not all(c == '*' for c in original_middle):
                    assert all(c == '*' for c in middle_section), (
                        f"Middle section of masked value should be asterisks, but got '{middle_section}'"
                    )
    
    @given(
        key=non_sensitive_keys,
        value=credential_values
    )
    def test_non_sensitive_parameters_not_masked(self, key, value):
        """
        Property 12: Credential Masking in Logs
        For any non-sensitive configuration parameter, the value 
        should not be masked and should remain unchanged.
        
        **Validates: Requirements 5.2**
        """
        masked_value = SecureConfigLogger.mask_sensitive_value(key, value)
        
        # Non-sensitive parameters should not be masked
        assert masked_value == value, (
            f"Non-sensitive parameter '{key}' with value '{value}' "
            f"should not be masked, but got '{masked_value}'"
        )
    
    @given(
        key=sensitive_keys,
        value=short_credential_values
    )
    def test_short_sensitive_values_completely_masked(self, key, value):
        """
        Property 12: Credential Masking in Logs
        For any sensitive parameter with a short value (≤4 characters),
        the entire value should be replaced with asterisks.
        
        **Validates: Requirements 5.2**
        """
        masked_value = SecureConfigLogger.mask_sensitive_value(key, value)
        
        # Short sensitive values should be completely masked
        expected_masked = "*" * len(value)
        assert masked_value == expected_masked, (
            f"Short sensitive value '{value}' should be completely masked as '{expected_masked}', "
            f"but got '{masked_value}'"
        )
        
        # Should have same length as original
        assert len(masked_value) == len(value), (
            f"Masked value length {len(masked_value)} should match original length {len(value)}"
        )
    
    @given(
        key=sensitive_keys,
        value=long_credential_values
    )
    def test_long_sensitive_values_partially_masked(self, key, value):
        """
        Property 12: Credential Masking in Logs
        For any sensitive parameter with a long value (>4 characters),
        only the middle portion should be masked, preserving first 2 
        and last 2 characters.
        
        **Validates: Requirements 5.2**
        """
        masked_value = SecureConfigLogger.mask_sensitive_value(key, value)
        
        # Long sensitive values should be partially masked
        expected_masked = value[:2] + "*" * (len(value) - 4) + value[-2:]
        assert masked_value == expected_masked, (
            f"Long sensitive value '{value}' should be masked as '{expected_masked}', "
            f"but got '{masked_value}'"
        )
        
        # Should preserve first 2 and last 2 characters
        assert masked_value[:2] == value[:2], (
            f"First 2 characters should be preserved: expected '{value[:2]}', "
            f"got '{masked_value[:2]}'"
        )
        assert masked_value[-2:] == value[-2:], (
            f"Last 2 characters should be preserved: expected '{value[-2:]}', "
            f"got '{masked_value[-2:]}'"
        )
        
        # Middle should be asterisks
        middle_part = masked_value[2:-2]
        assert all(c == '*' for c in middle_part), (
            f"Middle part '{middle_part}' should be all asterisks"
        )
        
        # Should have same length as original
        assert len(masked_value) == len(value), (
            f"Masked value length {len(masked_value)} should match original length {len(value)}"
        )
    
    @given(
        key=st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(
                min_codepoint=32,
                max_codepoint=126,
                blacklist_characters='\n\r\t\0'
            )
        ).filter(lambda x: x.strip() and '\x00' not in x),
        value=st.just("")
    )
    def test_empty_values_handled_correctly(self, key, value):
        """
        Property 12: Credential Masking in Logs
        For any parameter with an empty value, the masking function
        should handle it gracefully without errors.
        
        **Validates: Requirements 5.2**
        """
        masked_value = SecureConfigLogger.mask_sensitive_value(key, value)
        
        # Empty values should remain empty
        assert masked_value == "", (
            f"Empty value should remain empty, but got '{masked_value}'"
        )
    
    @given(
        config_dict=st.dictionaries(
            keys=st.sampled_from([
                "host", "port", "username", "password", 
                "secret_key", "api_token", "service_name"
            ]),
            values=credential_values,
            min_size=1,
            max_size=10
        )
    )
    def test_safe_config_summary_masks_sensitive_fields(self, config_dict):
        """
        Property 12: Credential Masking in Logs
        For any configuration dictionary containing both sensitive and 
        non-sensitive parameters, the safe summary should mask only 
        the sensitive parameters.
        
        **Validates: Requirements 5.2**
        """
        safe_summary = SecureConfigLogger.get_safe_config_summary(config_dict)
        
        # Should have same keys as original
        assert set(safe_summary.keys()) == set(config_dict.keys()), (
            f"Safe summary keys {set(safe_summary.keys())} should match "
            f"original keys {set(config_dict.keys())}"
        )
        
        # Check each field individually
        for key, original_value in config_dict.items():
            safe_value = safe_summary[key]
            expected_masked = SecureConfigLogger.mask_sensitive_value(key, str(original_value))
            
            assert safe_value == expected_masked, (
                f"Field '{key}' with value '{original_value}' should be masked as "
                f"'{expected_masked}', but got '{safe_value}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])