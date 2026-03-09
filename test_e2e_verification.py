"""
End-to-End Integration Tests for Verification Flow

This test suite verifies the complete verification flow from API request
through analyzers and back to the response.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.verification_engine import VerificationEngine
from src.models import VerificationResult, AnalysisResult, Finding


class TestEndToEndVerification:
    """Test end-to-end verification flows"""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients to avoid actual AWS calls"""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def verification_engine(self, mock_aws_clients):
        """Create verification engine with mocked AWS clients"""
        return VerificationEngine(aws_region='us-east-1')
    
    @pytest.mark.asyncio
    async def test_text_verification_end_to_end(self, verification_engine):
        """Test complete text verification flow"""
        # Mock text analyzer
        mock_text_result = AnalysisResult(
            analyzer_type='text',
            score=45.0,
            confidence=0.8,
            findings=[
                Finding(
                    type='sentiment_analysis',
                    severity='medium',
                    description='Content shows high emotional intensity'
                )
            ],
            metadata={'word_count': 50}
        )
        
        with patch.object(
            verification_engine.text_analyzer,
            'analyze',
            new=AsyncMock(return_value=mock_text_result)
        ):
            # Execute verification
            test_content = b"This is a test message about breaking news"
            result = await verification_engine.verify_content(
                content_type='text',
                content_data=test_content,
                language='en'
            )
            
            # Verify result structure
            assert isinstance(result, VerificationResult)
            assert result.content_type == 'text'
            assert 0 <= result.credibility_score <= 100
            assert result.classification in ['Fake', 'Misinformation', 'Bias', 'Misleading', 'Verified']
            assert 0 <= result.confidence <= 1
            assert len(result.explanation) > 0
            assert result.id is not None
            assert result.timestamp > 0
            
            # Verify classification logic
            # Score of 45 should result in Misinformation or Misleading
            assert result.classification in ['Misinformation', 'Misleading']
    
    @pytest.mark.asyncio
    async def test_image_verification_end_to_end(self, verification_engine):
        """Test complete image verification flow with OCR"""
        # Mock image analyzer with extracted text
        mock_image_result = AnalysisResult(
            analyzer_type='image',
            score=60.0,
            confidence=0.75,
            findings=[
                Finding(
                    type='manipulation_detection',
                    severity='low',
                    description='No significant manipulation detected'
                )
            ],
            metadata={'has_text': True}
        )
        # Store extracted text in metadata instead
        mock_image_result.metadata['extracted_text'] = "Breaking: Important news update"
        
        # Mock text analyzer for extracted text
        mock_text_result = AnalysisResult(
            analyzer_type='text',
            score=55.0,
            confidence=0.7,
            findings=[
                Finding(
                    type='linguistic_analysis',
                    severity='medium',
                    description='Clickbait language detected'
                )
            ],
            metadata={}
        )
        
        # Mock the verification engine's multimodal analysis to return both results
        async def mock_analyze_image_multimodal(content_data, language):
            return [mock_image_result, mock_text_result]
        
        with patch.object(
            verification_engine,
            '_analyze_image_multimodal',
            new=mock_analyze_image_multimodal
        ):
            # Execute verification
            test_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Fake PNG header
            result = await verification_engine.verify_content(
                content_type='image',
                content_data=test_image,
                language='en'
            )
            
            # Verify result structure
            assert isinstance(result, VerificationResult)
            assert result.content_type == 'image'
            assert 0 <= result.credibility_score <= 100
            assert result.classification in ['Fake', 'Misinformation', 'Bias', 'Misleading', 'Verified']
            
            # Verify multi-modal analysis (image + text from OCR)
            assert 'image_analysis' in result.analysis_details
            assert 'text_analysis' in result.analysis_details
    
    @pytest.mark.asyncio
    async def test_video_verification_end_to_end(self, verification_engine):
        """Test complete video verification flow with keyframes and transcription"""
        # Mock video analyzer with transcription
        mock_video_result = AnalysisResult(
            analyzer_type='video',
            score=70.0,
            confidence=0.8,
            findings=[
                Finding(
                    type='deepfake_detection',
                    severity='low',
                    description='No deepfake indicators detected'
                )
            ],
            metadata={'duration': 30}
        )
        # Store transcription in metadata instead
        mock_video_result.metadata['audio_transcription'] = "This is the audio transcription from the video"
        
        # Mock text analyzer for transcription
        mock_text_result = AnalysisResult(
            analyzer_type='text',
            score=75.0,
            confidence=0.85,
            findings=[],
            metadata={}
        )
        
        # Mock the verification engine's multimodal analysis to return both results
        async def mock_analyze_video_multimodal(content_data, language):
            return [mock_video_result, mock_text_result]
        
        with patch.object(
            verification_engine,
            '_analyze_video_multimodal',
            new=mock_analyze_video_multimodal
        ):
            # Execute verification
            test_video = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 100  # Fake MP4 header
            result = await verification_engine.verify_content(
                content_type='video',
                content_data=test_video,
                language='en'
            )
            
            # Verify result structure
            assert isinstance(result, VerificationResult)
            assert result.content_type == 'video'
            assert 0 <= result.credibility_score <= 100
            assert result.classification in ['Fake', 'Misinformation', 'Bias', 'Misleading', 'Verified']
            
            # Verify multi-modal analysis (video + transcription)
            assert 'video_analysis' in result.analysis_details
            assert 'text_analysis' in result.analysis_details
            
            # Score around 70-75 should result in Verified
            assert result.classification == 'Verified'
    
    @pytest.mark.asyncio
    async def test_credibility_score_calculation(self, verification_engine):
        """Test credibility score aggregation from multiple analyzers"""
        # Create multiple analysis results with different scores
        results = [
            AnalysisResult(
                analyzer_type='text',
                score=80.0,
                confidence=0.9,
                findings=[],
                metadata={}
            ),
            AnalysisResult(
                analyzer_type='image',
                score=60.0,
                confidence=0.7,
                findings=[],
                metadata={}
            )
        ]
        
        # Calculate aggregated score
        score = verification_engine.calculate_credibility_score(results)
        
        # Verify score is within bounds
        assert 0 <= score <= 100
        
        # Verify weighted average (text has higher weight)
        # Expected: (80 * 1.0 * 0.9 + 60 * 0.9 * 0.7) / (1.0 * 0.9 + 0.9 * 0.7)
        expected = (80 * 1.0 * 0.9 + 60 * 0.9 * 0.7) / (1.0 * 0.9 + 0.9 * 0.7)
        assert abs(score - expected) < 0.1
    
    @pytest.mark.asyncio
    async def test_classification_assignment(self, verification_engine):
        """Test classification assignment based on score and findings"""
        # Test Fake classification (score < 30)
        findings_fake = [
            Finding(type='database_match', severity='high', description='Known fake news')
        ]
        classification = verification_engine.assign_classification(25.0, findings_fake)
        assert classification == 'Fake'
        
        # Test Verified classification (score >= 70)
        findings_verified = []
        classification = verification_engine.assign_classification(75.0, findings_verified)
        assert classification == 'Verified'
        
        # Test Misinformation (30-50 with factual inaccuracies)
        findings_misinfo = [
            Finding(type='fact_check', severity='high', description='Factual inaccuracies detected')
        ]
        classification = verification_engine.assign_classification(40.0, findings_misinfo)
        assert classification in ['Misinformation', 'Misleading']
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_content(self, verification_engine):
        """Test error handling for empty content"""
        with pytest.raises(ValueError, match="Content data cannot be empty"):
            await verification_engine.verify_content(
                content_type='text',
                content_data=b"",
                language='en'
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_content_type(self, verification_engine):
        """Test error handling for invalid content type"""
        with pytest.raises(ValueError, match="Invalid content type"):
            await verification_engine.verify_content(
                content_type='invalid',
                content_data=b"test content",
                language='en'
            )
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, verification_engine):
        """Test that verification results can be cached (simulated)"""
        # This test verifies the result structure is suitable for caching
        mock_text_result = AnalysisResult(
            analyzer_type='text',
            score=80.0,
            confidence=0.9,
            findings=[],
            metadata={}
        )
        
        with patch.object(
            verification_engine.text_analyzer,
            'analyze',
            new=AsyncMock(return_value=mock_text_result)
        ):
            test_content = b"Test content for caching"
            result = await verification_engine.verify_content(
                content_type='text',
                content_data=test_content,
                language='en'
            )
            
            # Verify result can be serialized (important for caching)
            result_dict = result.model_dump()
            assert isinstance(result_dict, dict)
            assert 'id' in result_dict
            assert 'credibility_score' in result_dict  # Use snake_case
            assert 'classification' in result_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
