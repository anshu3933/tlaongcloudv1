"""Test SafeDate type decorator functionality"""
import pytest
from datetime import date, datetime
from src.models.type_decorators import SafeDate


class TestSafeDate:
    """Test the SafeDate TypeDecorator implementation"""
    
    def setup_method(self):
        """Set up test instance"""
        self.safe_date = SafeDate()
        self.dialect = None  # Mock dialect, not used in our implementation
    
    def test_none_value(self):
        """Test that None values pass through unchanged"""
        result = self.safe_date.process_bind_param(None, self.dialect)
        assert result is None
    
    def test_date_object(self):
        """Test that date objects pass through unchanged"""
        test_date = date(2025, 1, 15)
        result = self.safe_date.process_bind_param(test_date, self.dialect)
        assert result == test_date
        assert isinstance(result, date)
    
    def test_datetime_object(self):
        """Test that datetime objects are converted to date"""
        test_datetime = datetime(2025, 1, 15, 10, 30, 45)
        result = self.safe_date.process_bind_param(test_datetime, self.dialect)
        assert result == date(2025, 1, 15)
        assert isinstance(result, date)
    
    def test_string_iso_format(self):
        """Test that ISO format strings are converted"""
        test_string = "2025-01-15"
        result = self.safe_date.process_bind_param(test_string, self.dialect)
        assert result == date(2025, 1, 15)
        assert isinstance(result, date)
    
    def test_string_slash_format(self):
        """Test that slash format strings are converted"""
        test_string = "2025/01/15"
        result = self.safe_date.process_bind_param(test_string, self.dialect)
        assert result == date(2025, 1, 15)
        assert isinstance(result, date)
    
    def test_string_us_format(self):
        """Test that US format strings are converted"""
        test_string = "01-15-2025"
        result = self.safe_date.process_bind_param(test_string, self.dialect)
        assert result == date(2025, 1, 15)
        assert isinstance(result, date)
    
    def test_invalid_string_format(self):
        """Test that invalid string formats raise ValueError"""
        with pytest.raises(ValueError, match="Invalid date string format"):
            self.safe_date.process_bind_param("not-a-date", self.dialect)
    
    def test_unsupported_type(self):
        """Test that unsupported types raise TypeError"""
        with pytest.raises(TypeError, match="SafeDate cannot convert type int"):
            self.safe_date.process_bind_param(12345, self.dialect)
    
    def test_process_result_value(self):
        """Test that result values pass through unchanged"""
        test_date = date(2025, 1, 15)
        result = self.safe_date.process_result_value(test_date, self.dialect)
        assert result == test_date


if __name__ == "__main__":
    pytest.main([__file__, "-v"])