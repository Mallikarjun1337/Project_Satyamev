"""
Unit and property-based tests for VerificationEngine
"""
import pytest
from hypothesis import given, strategies as st
from src.verification_engine import VerificationEngine
from src.models import AnalysisResult, Finding

@pytest.fixture
def engine():
    return VerificationEngine()

class TestVerificationEngine:
    """Unit tests for VerificationEngine"""
    
    def test_engine_initialization(self, engine):
        """Test that engine initializes with all analyzers"""
        assert engine.text_analyzer is not None
        assert engine.image_analyzer is not None
        assert engine.video_analyzer is not None
    
    def test_calculate_credibility_score_empty(self, engine):
        """Test credibility score calculation with empty results"""
        score = engine.calculate_credibility_score([])
        assert score == 0.0
    
    def test_calculate_credibility_score_single(self, engine):
        """Test credibility score calculation with single result"""
        result = AnalysisResult(
            analyzer_type='text',
            score=75.0,
            confidence=0.8,
            findings=[],
            metadata={}
        )
        score = engine.calculate_credibility_score([result])
        assert score == 75.0
    
    def test_assign_classification_fake(self, engine):
        """Test classification assignment for fake content (score < 30)"""
        classification = engine.assign_classification(25.0, [])
        assert classification == 'Fake'
    
    def test_assign_classification_verified(self, engine):
        """Test classification assignment for verified content (score >= 70)"""
        classification = engine.assign_classification(75.0, [])
        assert classification == 'Verified'

# Feature: satyamev-vijayate, Property 2: Analysis Result Aggregation
@given(st.lists(
    st.builds(
        AnalysisResult,
        analyzer_type=st.sampled_from(['text', 'image', 'video']),
        score=st.floats(min_value=0, max_value=100),
        confidence=st.floats(min_value=0, max_value=1),
        findings=st.just([]),
        metadata=st.just({})
    ),
    min_size=1,
    max_size=3
))
def test_aggregation_produces_valid_score(analysis_results):
    """
    Property: For any set of analysis results, aggregation produces score 0-100
    """
    engine = VerificationEngine()
    score = engine.calculate_credibility_score(analysis_results)
    assert 0 <= score <= 100

# Feature: satyamev-vijayate, Property 10: Fake Classification Rule
@given(st.floats(min_value=0, max_value=29.99))
def test_fake_classification_rule(score):
    """
    Property: For any credibility score below 30, classification should be "Fake"
    """
    engine = VerificationEngine()
    classification = engine.assign_classification(score, [])
    assert classification == 'Fake'

# Feature: satyamev-vijayate, Property 14: Verified Classification Rule
@given(st.floats(min_value=70, max_value=100))
def test_verified_classification_rule(score):
    """
    Property: For any credibility score above 70, classification should be "Verified"
    """
    engine = VerificationEngine()
    classification = engine.assign_classification(score, [])
    assert classification == 'Verified'
