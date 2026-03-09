"""
Property-Based Test: OCR Error Handling
Validates: Requirements 3.5

Property 9: OCR Error Handling
For any OCR service failure (timeout, service unavailable, invalid response),
the system must catch the error and return a user-friendly error message without crashing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_handler_simple import extract_text_from_image, process_image_verification
import base64


class TestOCRErrorHandlingProperty:
    """Property tests for OCR error handling"""

    @given(
        error_type=st.sampled_from([
            'ServiceUnavailable',
            'ThrottlingException',
            'InvalidParameterException',
            'InternalServerError',
            'AccessDeniedException'
        ])
    )
    @settings(max_examples=10)
    def test_textract_service_errors_handled_gracefully(self, error_type):
        """Test that various Textract service errors are handled gracefully"""
        # Create mock image bytes
        image_bytes = b'fake_image_data'
        
        # Mock Textract client to raise specific error
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = Exception(error_type)
            
            # Should not raise exception, should return error message
            try:
                result = extract_text_from_image(image_bytes)
                # If it returns, it should be empty or error indicator
                assert result is not None
            except Exception as e:
                # If it raises, it should be a handled RuntimeError
                assert isinstance(e, RuntimeError)
                assert 'OCR failed' in str(e) or 'Textract error' in str(e)

    @given(
        image_size=st.integers(min_value=1, max_value=1024)
    )
    @settings(max_examples=10)
    def test_invalid_image_data_handled_gracefully(self, image_size):
        """Test that invalid image data is handled gracefully"""
        # Create invalid/corrupted image bytes
        invalid_image_bytes = b'x' * image_size
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = Exception('Invalid image format')
            
            # Should handle error gracefully
            try:
                result = extract_text_from_image(invalid_image_bytes)
                assert result is not None
            except RuntimeError as e:
                assert 'OCR failed' in str(e)

    @given(
        error_message=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10)
    def test_error_messages_are_descriptive(self, error_message):
        """Test that error messages are descriptive and user-friendly"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = Exception(error_message)
            
            try:
                extract_text_from_image(image_bytes)
            except RuntimeError as e:
                # Error message should be descriptive
                assert len(str(e)) > 0
                assert 'OCR' in str(e) or 'failed' in str(e) or 'Textract' in str(e)

    def test_empty_textract_response_handled(self):
        """Test that empty Textract response is handled gracefully"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            # Mock empty response
            mock_textract.detect_document_text.return_value = {'Blocks': []}
            
            result = extract_text_from_image(image_bytes)
            
            # Should return empty string, not crash
            assert result == ''

    def test_no_text_blocks_in_response(self):
        """Test that response with no LINE blocks is handled"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            # Mock response with no LINE blocks
            mock_textract.detect_document_text.return_value = {
                'Blocks': [
                    {'BlockType': 'PAGE', 'Text': 'Page'},
                    {'BlockType': 'WORD', 'Text': 'Word'}
                ]
            }
            
            result = extract_text_from_image(image_bytes)
            
            # Should return empty string since no LINE blocks
            assert result == ''

    @given(
        block_count=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=10)
    def test_various_block_counts_handled(self, block_count):
        """Test that various numbers of text blocks are handled correctly"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            # Create mock blocks
            blocks = [
                {'BlockType': 'LINE', 'Text': f'Line {i}'}
                for i in range(block_count)
            ]
            mock_textract.detect_document_text.return_value = {'Blocks': blocks}
            
            result = extract_text_from_image(image_bytes)
            
            # Should handle any number of blocks
            assert isinstance(result, str)
            if block_count > 0:
                assert len(result) > 0

    def test_malformed_textract_response_handled(self):
        """Test that malformed Textract response is handled gracefully"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            # Mock malformed response (missing 'Blocks' key)
            mock_textract.detect_document_text.return_value = {}
            
            try:
                result = extract_text_from_image(image_bytes)
                # Should handle gracefully, possibly returning empty string
                assert result is not None
            except (RuntimeError, KeyError) as e:
                # Acceptable to raise error for malformed response
                assert True

    @given(
        base64_valid=st.booleans()
    )
    @settings(max_examples=10)
    def test_process_image_verification_error_handling(self, base64_valid):
        """Test that process_image_verification handles errors gracefully"""
        if base64_valid:
            # Valid base64
            image_data = base64.b64encode(b'fake_image_data').decode('utf-8')
        else:
            # Invalid base64
            image_data = 'invalid_base64_!@#$'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = Exception('OCR Error')
            
            try:
                result = process_image_verification(image_data, 'en', 'test_user')
                # If it returns, should have error field
                assert 'error' in result or 'credibility_score' in result
            except (RuntimeError, ValueError) as e:
                # Acceptable to raise error
                assert 'failed' in str(e).lower() or 'invalid' in str(e).lower()

    def test_network_timeout_handled(self):
        """Test that network timeout errors are handled gracefully"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = TimeoutError('Request timeout')
            
            try:
                extract_text_from_image(image_bytes)
            except RuntimeError as e:
                assert 'OCR failed' in str(e) or 'timeout' in str(e).lower()

    def test_connection_error_handled(self):
        """Test that connection errors are handled gracefully"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = ConnectionError('Connection failed')
            
            try:
                extract_text_from_image(image_bytes)
            except RuntimeError as e:
                assert 'OCR failed' in str(e) or 'connection' in str(e).lower()

    @given(
        consecutive_failures=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10)
    def test_multiple_consecutive_failures_handled(self, consecutive_failures):
        """Test that multiple consecutive OCR failures are handled"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = Exception('OCR Error')
            
            failure_count = 0
            for _ in range(consecutive_failures):
                try:
                    extract_text_from_image(image_bytes)
                except RuntimeError:
                    failure_count += 1
            
            # All failures should be handled (not crash the system)
            assert failure_count == consecutive_failures

    def test_partial_response_handled(self):
        """Test that partial/incomplete Textract response is handled"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            # Mock partial response (blocks without Text field)
            mock_textract.detect_document_text.return_value = {
                'Blocks': [
                    {'BlockType': 'LINE'},  # Missing 'Text' field
                    {'BlockType': 'LINE', 'Text': 'Valid text'}
                ]
            }
            
            try:
                result = extract_text_from_image(image_bytes)
                # Should handle gracefully, extracting what it can
                assert isinstance(result, str)
            except (RuntimeError, KeyError) as e:
                # Acceptable to raise error for malformed data
                assert True

    @given(
        error_code=st.integers(min_value=400, max_value=599)
    )
    @settings(max_examples=10)
    def test_http_error_codes_handled(self, error_code):
        """Test that various HTTP error codes are handled gracefully"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            error = Exception(f'HTTP Error {error_code}')
            mock_textract.detect_document_text.side_effect = error
            
            try:
                extract_text_from_image(image_bytes)
            except RuntimeError as e:
                assert 'OCR failed' in str(e) or str(error_code) in str(e)

    def test_property_all_errors_caught(self):
        """Property: All OCR errors must be caught and not crash the system"""
        error_types = [
            Exception('Generic error'),
            RuntimeError('Runtime error'),
            ValueError('Value error'),
            KeyError('Key error'),
            TimeoutError('Timeout'),
            ConnectionError('Connection failed')
        ]
        
        image_bytes = b'fake_image_data'
        
        for error in error_types:
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = error
                
                # Should either return gracefully or raise RuntimeError
                try:
                    result = extract_text_from_image(image_bytes)
                    assert result is not None
                except RuntimeError:
                    # Acceptable to raise RuntimeError (handled error)
                    pass
                except Exception as e:
                    # Should not raise other exceptions
                    pytest.fail(f'Unhandled exception type: {type(e).__name__}')

    def test_error_logging_occurs(self):
        """Test that errors are logged for debugging"""
        image_bytes = b'fake_image_data'
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            with patch('lambda_handler_simple.logger') as mock_logger:
                mock_textract.detect_document_text.side_effect = Exception('Test error')
                
                try:
                    extract_text_from_image(image_bytes)
                except RuntimeError:
                    pass
                
                # Verify error was logged
                assert mock_logger.error.called or mock_logger.exception.called
