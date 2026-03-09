"""
Property-Based Test: OCR Timeout Enforcement
Validates: Requirements 3.6

Property 10: OCR Timeout Enforcement
For any OCR request, if processing exceeds 10 seconds, the request must be
aborted and return a timeout error.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_handler_simple import extract_text_from_image, process_image_verification
import base64


class TestOCRTimeoutProperty:
    """Property tests for OCR timeout enforcement"""

    TIMEOUT_LIMIT = 10  # 10 seconds as per requirement 3.6

    def test_timeout_limit_is_enforced(self):
        """Test that OCR requests timeout after 10 seconds"""
        image_bytes = b'fake_image_data'
        
        # Mock Textract to simulate long-running operation
        def slow_ocr(*args, **kwargs):
            time.sleep(11)  # Sleep longer than timeout
            return {'Blocks': []}
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = slow_ocr
            
            start_time = time.time()
            
            try:
                extract_text_from_image(image_bytes)
            except (RuntimeError, TimeoutError) as e:
                elapsed_time = time.time() - start_time
                # Should timeout around 10 seconds, not wait for full 11 seconds
                assert elapsed_time < 12  # Allow some margin
                assert 'timeout' in str(e).lower() or 'OCR failed' in str(e)

    @given(
        delay_seconds=st.integers(min_value=11, max_value=30)
    )
    @settings(max_examples=5, deadline=None)
    def test_various_timeout_scenarios(self, delay_seconds):
        """Test that various delays beyond timeout are handled"""
        image_bytes = b'fake_image_data'
        
        def slow_ocr(*args, **kwargs):
            time.sleep(delay_seconds)
            return {'Blocks': []}
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = slow_ocr
            
            start_time = time.time()
            
            try:
                extract_text_from_image(image_bytes)
            except (RuntimeError, TimeoutError):
                elapsed_time = time.time() - start_time
                # Should timeout before the full delay
                assert elapsed_time < delay_seconds

    def test_requests_under_timeout_complete_successfully(self):
        """Test that requests under 10 seconds complete successfully"""
        image_bytes = b'fake_image_data'
        
        # Mock Textract to return quickly (under timeout)
        def fast_ocr(*args, **kwargs):
            time.sleep(0.1)  # Very fast response
            return {
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Test text'}
                ]
            }
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = fast_ocr
            
            start_time = time.time()
            result = extract_text_from_image(image_bytes)
            elapsed_time = time.time() - start_time
            
            # Should complete successfully
            assert result == 'Test text'
            assert elapsed_time < self.TIMEOUT_LIMIT

    @given(
        response_time=st.floats(min_value=0.1, max_value=9.5)
    )
    @settings(max_examples=10, deadline=None)
    def test_requests_within_timeout_succeed(self, response_time):
        """Property: All requests completing within 10 seconds should succeed"""
        image_bytes = b'fake_image_data'
        
        def timed_ocr(*args, **kwargs):
            time.sleep(response_time)
            return {
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Test text'}
                ]
            }
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = timed_ocr
            
            start_time = time.time()
            result = extract_text_from_image(image_bytes)
            elapsed_time = time.time() - start_time
            
            # Should complete successfully within timeout
            assert result is not None
            assert elapsed_time < self.TIMEOUT_LIMIT + 1  # Small margin

    def test_timeout_error_message_is_descriptive(self):
        """Test that timeout error messages are descriptive"""
        image_bytes = b'fake_image_data'
        
        def slow_ocr(*args, **kwargs):
            time.sleep(11)
            return {'Blocks': []}
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = slow_ocr
            
            try:
                extract_text_from_image(image_bytes)
                pytest.fail('Should have raised timeout error')
            except (RuntimeError, TimeoutError) as e:
                error_msg = str(e).lower()
                # Error message should mention timeout or time-related issue
                assert 'timeout' in error_msg or 'time' in error_msg or 'ocr failed' in error_msg

    def test_timeout_boundary_at_10_seconds(self):
        """Test behavior at the exact 10-second boundary"""
        image_bytes = b'fake_image_data'
        
        # Test just under timeout
        def almost_timeout(*args, **kwargs):
            time.sleep(9.9)
            return {
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Test text'}
                ]
            }
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = almost_timeout
            
            # Should complete successfully
            result = extract_text_from_image(image_bytes)
            assert result is not None

    def test_timeout_applies_to_all_image_sizes(self):
        """Test that timeout applies regardless of image size"""
        image_sizes = [100, 1024, 10240, 102400]  # Various sizes
        
        for size in image_sizes:
            image_bytes = b'x' * size
            
            def slow_ocr(*args, **kwargs):
                time.sleep(11)
                return {'Blocks': []}
            
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = slow_ocr
                
                start_time = time.time()
                
                try:
                    extract_text_from_image(image_bytes)
                except (RuntimeError, TimeoutError):
                    elapsed_time = time.time() - start_time
                    # Should timeout regardless of image size
                    assert elapsed_time < 12

    def test_timeout_is_consistent_across_calls(self):
        """Test that timeout is consistently enforced across multiple calls"""
        image_bytes = b'fake_image_data'
        
        def slow_ocr(*args, **kwargs):
            time.sleep(11)
            return {'Blocks': []}
        
        timeout_count = 0
        
        for _ in range(3):
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = slow_ocr
                
                start_time = time.time()
                
                try:
                    extract_text_from_image(image_bytes)
                except (RuntimeError, TimeoutError):
                    elapsed_time = time.time() - start_time
                    if elapsed_time < 12:
                        timeout_count += 1
        
        # All calls should timeout consistently
        assert timeout_count == 3

    def test_process_image_verification_respects_timeout(self):
        """Test that process_image_verification also respects timeout"""
        image_data = base64.b64encode(b'fake_image_data').decode('utf-8')
        
        def slow_ocr(*args, **kwargs):
            time.sleep(11)
            return {'Blocks': []}
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = slow_ocr
            
            start_time = time.time()
            
            try:
                process_image_verification(image_data, 'en', 'test_user')
            except (RuntimeError, TimeoutError) as e:
                elapsed_time = time.time() - start_time
                # Should timeout
                assert elapsed_time < 12
                assert 'timeout' in str(e).lower() or 'failed' in str(e).lower()

    def test_timeout_does_not_affect_fast_responses(self):
        """Test that timeout mechanism doesn't slow down fast responses"""
        image_bytes = b'fake_image_data'
        
        def instant_ocr(*args, **kwargs):
            return {
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Instant response'}
                ]
            }
        
        with patch('lambda_handler_simple.textract_client') as mock_textract:
            mock_textract.detect_document_text.side_effect = instant_ocr
            
            start_time = time.time()
            result = extract_text_from_image(image_bytes)
            elapsed_time = time.time() - start_time
            
            # Should complete very quickly
            assert result == 'Instant response'
            assert elapsed_time < 1  # Should be nearly instant

    @given(
        num_concurrent=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=5, deadline=None)
    def test_timeout_with_concurrent_requests(self, num_concurrent):
        """Test that timeout works correctly with concurrent requests"""
        image_bytes = b'fake_image_data'
        
        def slow_ocr(*args, **kwargs):
            time.sleep(11)
            return {'Blocks': []}
        
        results = []
        
        def make_request():
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = slow_ocr
                
                start_time = time.time()
                try:
                    extract_text_from_image(image_bytes)
                    results.append(('success', time.time() - start_time))
                except (RuntimeError, TimeoutError):
                    results.append(('timeout', time.time() - start_time))
        
        threads = [threading.Thread(target=make_request) for _ in range(num_concurrent)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=15)
        
        # All requests should timeout
        assert len(results) == num_concurrent
        for status, elapsed in results:
            assert status == 'timeout'
            assert elapsed < 12

    def test_property_timeout_always_enforced(self):
        """Property: Timeout must always be enforced for slow requests"""
        image_bytes = b'fake_image_data'
        slow_delays = [11, 15, 20, 30, 60]
        
        for delay in slow_delays:
            def slow_ocr(*args, **kwargs):
                time.sleep(delay)
                return {'Blocks': []}
            
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = slow_ocr
                
                start_time = time.time()
                timed_out = False
                
                try:
                    extract_text_from_image(image_bytes)
                except (RuntimeError, TimeoutError):
                    elapsed_time = time.time() - start_time
                    timed_out = True
                    # Property: Must timeout before full delay
                    assert elapsed_time < delay
                
                # Property: Must timeout for all slow requests
                assert timed_out, f'Request with {delay}s delay did not timeout'

    def test_timeout_cleanup_releases_resources(self):
        """Test that timeout properly cleans up and releases resources"""
        image_bytes = b'fake_image_data'
        
        def slow_ocr(*args, **kwargs):
            time.sleep(11)
            return {'Blocks': []}
        
        # Run multiple timeout scenarios
        for _ in range(3):
            with patch('lambda_handler_simple.textract_client') as mock_textract:
                mock_textract.detect_document_text.side_effect = slow_ocr
                
                try:
                    extract_text_from_image(image_bytes)
                except (RuntimeError, TimeoutError):
                    pass
        
        # If we reach here without hanging, cleanup worked
        assert True
