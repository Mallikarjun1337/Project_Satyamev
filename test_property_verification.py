"""
Property-based tests for verification engine and classification rules.

Feature: satyamev-vijayate
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from src.models import (
    AnalysisResult,
    Finding,
    get_classification,
    CLASSIFICATION_FAKE,
    CLASSIFICATION_MISINFORMATION,
    CLASSIFICATION_BIAS,
    CLASSIFICATION_MISLEADING,
    CLASSIFICATION_VERIFIED,
    SCORE_THRESHOLD_FAKE,
    SCORE_THRESHOLD_MISINFORMATION_MIN,
    SCORE_THRESHOLD_MISINFORMATION_MAX,
    SCORE_THRESHOLD_BIAS_MIN,
    SCORE_THRESHOLD_BIAS_MAX,
    SCORE_THRESHOLD_MISLEADING_MIN,
    SCORE_THRESHOLD_MISLEADING_MAX,
    SCORE_THRESHOLD_VERIFIED,
)
from src.verification_engine import VerificationEngine


# Strategy for generating Finding objects
finding_strategy = st.builds(
    Finding,
    type=st.sampled_from([
        'factual_error', 'false_claim', 'unverified_claim',
        'political_bias', 'ideological_bias', 'partisan_language',
        'misleading_context', 'cherry_picking', 'false_equivalence', 'out_of_context',
        'database_match', 'manipulation_detected', 'sentiment_anomaly',
        'deepfake_indicator', 'ocr_mismatch', 'reverse_search_hit'
    ]),
    severity=st.sampled_from(['low', 'medium', 'high']),
    description=st.text(min_size=1, max_size=100),
    evidence=st.none()
)

# Strategy for generating AnalysisResult objects
analysis_result_strategy = st.builds(
    AnalysisResult,
    analyzer_type=st.sampled_from(['text', 'image', 'video']),
    score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    findings=st.lists(finding_strategy, min_size=0, max_size=10),
    metadata=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
        max_size=5
    )
)


# ============================================================================
# Task 4.4: Property 2 - Analysis Result Aggregation
# ============================================================================

@pytest.mark.property
@settings(max_examples=100, deadline=None)  # Disable deadline due to AWS client initialization
@given(analysis_results=st.lists(analysis_result_strategy, min_size=1, max_size=10))
def test_analysis_result_aggregation(analysis_results: list):
    """
    Property 2: Analysis Result Aggregation
    
    **Validates: Requirements 7.6**
    
    For any set of individual analysis results, combining them should produce
    a single credibility score between 0 and 100.
    """
    # Arrange
    engine = VerificationEngine()
    
    # Act
    credibility_score = engine.calculate_credibility_score(analysis_results)
    
    # Assert
    assert 0.0 <= credibility_score <= 100.0, (
        f"Credibility score {credibility_score} is outside valid range [0, 100]. "
        f"Analysis results: {len(analysis_results)} items"
    )
    assert isinstance(credibility_score, float), (
        f"Credibility score must be a float, got {type(credibility_score)}"
    )


# ============================================================================
# Task 4.6: Classification Rule Properties
# ============================================================================

@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    findings=st.lists(finding_strategy, min_size=0, max_size=20)
)
def test_classification_assignment(credibility_score: float, findings: list):
    """
    Property 8: Classification Assignment
    
    **Validates: Requirements 16.1, 16.2**
    
    For any verification result, exactly one classification category
    (Fake, Misinformation, Bias, Misleading, or Verified) should be assigned.
    """
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert - exactly one classification is returned
    assert classification is not None, "Classification must not be None"
    assert isinstance(classification, str), f"Classification must be a string, got {type(classification)}"
    
    # Assert - it's one of the valid categories
    valid_categories = {
        CLASSIFICATION_FAKE,
        CLASSIFICATION_MISINFORMATION,
        CLASSIFICATION_BIAS,
        CLASSIFICATION_MISLEADING,
        CLASSIFICATION_VERIFIED,
    }
    assert classification in valid_categories, (
        f"Classification '{classification}' is not one of the valid categories: {valid_categories}"
    )


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(min_value=0.0, max_value=SCORE_THRESHOLD_FAKE - 0.01, allow_nan=False, allow_infinity=False),
    findings=st.lists(finding_strategy, min_size=0, max_size=20)
)
def test_fake_classification_rule(credibility_score: float, findings: list):
    """
    Property 10: Fake Classification Rule
    
    **Validates: Requirements 16.3**
    
    For any credibility score below 30 (strictly less than 30), 
    the classification should be "Fake".
    
    Note: Requirement 16.3 states "below 30" which means < 30, not <= 30.
    The boundary case of exactly 30.0 falls under the Misinformation rule (16.4).
    """
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    assert classification == CLASSIFICATION_FAKE, (
        f"Expected classification 'Fake' for score {credibility_score:.2f} (< 30), "
        f"but got '{classification}'"
    )


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(
        min_value=SCORE_THRESHOLD_MISINFORMATION_MIN,
        max_value=SCORE_THRESHOLD_MISINFORMATION_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    has_factual_inaccuracies=st.booleans()
)
def test_misinformation_classification_rule(credibility_score: float, has_factual_inaccuracies: bool):
    """
    Property 11: Misinformation Classification Rule
    
    **Validates: Requirements 16.4**
    
    For any credibility score between 30 and 50 where analysis results indicate
    factual inaccuracies, the classification should be "Misinformation".
    """
    # Arrange - create findings with or without factual inaccuracies
    if has_factual_inaccuracies:
        findings = [
            Finding(
                type='factual_error',
                severity='high',
                description='Contains factual inaccuracies'
            )
        ]
    else:
        findings = [
            Finding(
                type='sentiment_anomaly',
                severity='low',
                description='Some other issue'
            )
        ]
    
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    if has_factual_inaccuracies:
        assert classification == CLASSIFICATION_MISINFORMATION, (
            f"Expected classification 'Misinformation' for score {credibility_score:.2f} "
            f"with factual inaccuracies, but got '{classification}'"
        )
    # Note: Without factual inaccuracies, the classification may fall back to other categories


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(
        min_value=SCORE_THRESHOLD_BIAS_MIN,
        max_value=SCORE_THRESHOLD_BIAS_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    has_political_slant=st.booleans()
)
def test_bias_classification_rule(credibility_score: float, has_political_slant: bool):
    """
    Property 12: Bias Classification Rule
    
    **Validates: Requirements 16.5**
    
    For any credibility score between 50 and 70 where analysis results indicate
    political or ideological slant, the classification should be "Bias".
    """
    # Arrange - create findings with or without political slant
    if has_political_slant:
        findings = [
            Finding(
                type='political_bias',
                severity='medium',
                description='Contains political or ideological slant'
            )
        ]
    else:
        findings = [
            Finding(
                type='sentiment_anomaly',
                severity='low',
                description='Some other issue'
            )
        ]
    
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    if has_political_slant:
        assert classification == CLASSIFICATION_BIAS, (
            f"Expected classification 'Bias' for score {credibility_score:.2f} "
            f"with political slant, but got '{classification}'"
        )
    # Note: Without political slant, the classification may fall back to other categories


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(
        min_value=SCORE_THRESHOLD_MISLEADING_MIN,
        max_value=SCORE_THRESHOLD_MISLEADING_MAX,
        allow_nan=False,
        allow_infinity=False
    ),
    has_deceptive_presentation=st.booleans()
)
def test_misleading_classification_rule(credibility_score: float, has_deceptive_presentation: bool):
    """
    Property 13: Misleading Classification Rule
    
    **Validates: Requirements 16.6**
    
    For any credibility score between 50 and 70 where analysis results indicate
    deceptive presentation, the classification should be "Misleading".
    """
    # Arrange - create findings with or without deceptive presentation
    if has_deceptive_presentation:
        findings = [
            Finding(
                type='misleading_context',
                severity='medium',
                description='Presents information in a deceptive manner'
            )
        ]
    else:
        findings = [
            Finding(
                type='sentiment_anomaly',
                severity='low',
                description='Some other issue'
            )
        ]
    
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    if has_deceptive_presentation:
        assert classification == CLASSIFICATION_MISLEADING, (
            f"Expected classification 'Misleading' for score {credibility_score:.2f} "
            f"with deceptive presentation, but got '{classification}'"
        )
    # Note: Without deceptive presentation, the classification may fall back to other categories


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(
        min_value=SCORE_THRESHOLD_VERIFIED + 0.01,  # "above 70" means > 70, not >= 70
        max_value=100.0,
        allow_nan=False,
        allow_infinity=False
    ),
    findings=st.lists(finding_strategy, min_size=0, max_size=20)
)
def test_verified_classification_rule(credibility_score: float, findings: list):
    """
    Property 14: Verified Classification Rule
    
    **Validates: Requirements 16.7**
    
    For any credibility score above 70 (strictly greater than 70), 
    the classification should be "Verified".
    
    Note: Requirement 16.7 states "above 70" which means > 70, not >= 70.
    The boundary case of exactly 70.0 falls under the Bias/Misleading rules (16.5, 16.6).
    """
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    assert classification == CLASSIFICATION_VERIFIED, (
        f"Expected classification 'Verified' for score {credibility_score:.2f} (> 70), "
        f"but got '{classification}'"
    )
