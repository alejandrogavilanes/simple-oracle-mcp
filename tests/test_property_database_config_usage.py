"""
Property-based test for DatabaseConfig model usage
Tests Property 15: DatabaseConfig Model Usage
"""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError
from config import DatabaseConfig


# Strategy for generating valid host names
valid_hosts = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip() and not x.startswith(' ') and not x.endswith(' '))

# Strategy for generating valid port numbers
valid_ports = st.integers(min_value=1, max_value=65535)

# Strategy for generating invalid port numbers
invalid_ports = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=65536)
)

# Strategy for generating valid service names
valid_service_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip() and not x.startswith(' ') and not x.endswith(' '))

# Strategy for generating valid usernames
valid_usernames = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip() and not x.startswith(' ') and not x.endswith(' '))

# Strategy for generating valid passwords
valid_passwords = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(
        min_codepoint=32,
        max_codepoint=126,
        blacklist_characters='\n\r\t\0'
    )
).filter(lambda x: x.strip() and not x.startswith(' ') and not x.endswith(' '))

# Strategy for generating valid timeout values
valid_timeouts = st.integers(min_value=1, max_value=3600)

# Strategy for generating invalid timeout values
invalid_timeouts = st.integers(max_value=0)

# Strategy for generating valid max_rows values
valid_max_rows = st.integers(min_value=1, max_value=10000)

# Strategy for generating invalid max_rows values
invalid_max_rows = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=10001)
)


class TestDatabaseConfigModelUsage:
    """Property-based tests for DatabaseConfig model usage"""
    
    @given(
        host=valid_hosts,
        port=valid_ports,
        service_name=valid_service_names,
        username=valid_usernames,
        password=valid_passwords,
        connection_timeout=valid_timeouts,
        query_timeout=valid_timeouts,
        max_rows=valid_max_rows
    )
    def test_valid_environment_parameters_create_valid_config(
        self, host, port, service_name, username, password, 
        connection_timeout, query_timeout, max_rows
    ):
        """
        Property 15: DatabaseConfig Model Usage
        For any valid environment parameters processed by the configuration system,
        the parameters should be validated through the existing DatabaseConfig model
        to ensure consistency.
        
        **Validates: Requirements 7.2**
        """
        # Create DatabaseConfig with valid parameters
        config = DatabaseConfig(
            host=host,
            port=port,
            service_name=service_name,
            username=username,
            password=password,
            connection_timeout=connection_timeout,
            query_timeout=query_timeout,
            max_rows=max_rows
        )
        
        # Verify all parameters are properly stored and accessible
        assert config.host == host
        assert config.port == port
        assert config.service_name == service_name
        assert config.username == username
        assert config.password == password
        assert config.connection_timeout == connection_timeout
        assert config.query_timeout == query_timeout
        assert config.max_rows == max_rows
        
        # Verify DSN property is correctly generated
        expected_dsn = f"{host}:{port}/{service_name}"
        assert config.dsn == expected_dsn
        
        # Verify source tracking functionality is available
        config.set_source_info("host", "test_source")
        sources = config.get_source_info()
        assert sources["host"] == "test_source"
        
        # Verify warning tracking functionality is available
        config.add_warning("test_warning")
        warnings = config.get_warnings()
        assert "test_warning" in warnings
    
    @given(
        host=valid_hosts,
        service_name=valid_service_names,
        username=valid_usernames,
        password=valid_passwords,
        port=invalid_ports
    )
    def test_invalid_port_parameters_raise_validation_error(
        self, host, service_name, username, password, port
    ):
        """
        Property 15: DatabaseConfig Model Usage
        For any invalid port parameters, the DatabaseConfig model should
        raise ValidationError to ensure consistency.
        
        **Validates: Requirements 7.2**
        """
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                host=host,
                port=port,
                service_name=service_name,
                username=username,
                password=password
            )
        
        # Verify the error is related to port validation
        error_str = str(exc_info.value).lower()
        assert "port" in error_str
    
    @given(
        host=valid_hosts,
        port=valid_ports,
        service_name=valid_service_names,
        username=valid_usernames,
        password=valid_passwords,
        connection_timeout=invalid_timeouts
    )
    def test_invalid_connection_timeout_raises_validation_error(
        self, host, port, service_name, username, password, connection_timeout
    ):
        """
        Property 15: DatabaseConfig Model Usage
        For any invalid timeout parameters, the DatabaseConfig model should
        raise ValidationError to ensure consistency.
        
        **Validates: Requirements 7.2**
        """
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                host=host,
                port=port,
                service_name=service_name,
                username=username,
                password=password,
                connection_timeout=connection_timeout
            )
        
        # Verify the error is related to timeout validation
        error_str = str(exc_info.value).lower()
        assert "timeout" in error_str
    
    @given(
        host=valid_hosts,
        port=valid_ports,
        service_name=valid_service_names,
        username=valid_usernames,
        password=valid_passwords,
        query_timeout=invalid_timeouts
    )
    def test_invalid_query_timeout_raises_validation_error(
        self, host, port, service_name, username, password, query_timeout
    ):
        """
        Property 15: DatabaseConfig Model Usage
        For any invalid query timeout parameters, the DatabaseConfig model should
        raise ValidationError to ensure consistency.
        
        **Validates: Requirements 7.2**
        """
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                host=host,
                port=port,
                service_name=service_name,
                username=username,
                password=password,
                query_timeout=query_timeout
            )
        
        # Verify the error is related to timeout validation
        error_str = str(exc_info.value).lower()
        assert "timeout" in error_str
    
    @given(
        host=valid_hosts,
        port=valid_ports,
        service_name=valid_service_names,
        username=valid_usernames,
        password=valid_passwords,
        max_rows=invalid_max_rows
    )
    def test_invalid_max_rows_raises_validation_error(
        self, host, port, service_name, username, password, max_rows
    ):
        """
        Property 15: DatabaseConfig Model Usage
        For any invalid max_rows parameters, the DatabaseConfig model should
        raise ValidationError to ensure consistency.
        
        **Validates: Requirements 7.2**
        """
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                host=host,
                port=port,
                service_name=service_name,
                username=username,
                password=password,
                max_rows=max_rows
            )
        
        # Verify the error is related to max_rows validation
        error_str = str(exc_info.value).lower()
        assert "max rows" in error_str or "max_rows" in error_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])