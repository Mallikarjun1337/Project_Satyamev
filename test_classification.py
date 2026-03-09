"""
Property-based tests for classification validity.

Feature: satyamev-vijayate
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.models import (
    get_classification,
    Finding,
    CLASSIFICATION_FAKE,
    CLASSIFICATION_MISINFORMATION,
    CLASSIFICATION_BIAS,
    CLASSIFICATION_MISLEADING,
    CLASSIFICATION_VERIFIED,
)

# Valid classification categories
VALID_CLASSIFICATIONS = {
    CLASSIFICATION_FAKE,
    CLASSIFICATION_MISINFORMATION,
    CLASSIFICATION_BIAS,
    CLASSIFICATION_MISLEADING,
    CLASSIFICATION_VERIFIED,
}

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


@pytest.mark.property
@settings(max_examples=100)
@given(
    credibility_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    findings=st.lists(finding_strategy, min_size=0, max_size=20)
)
def test_classification_validity(credibility_score: float, findings: list):
    """
    Property 9: Classification Validity
    
    **Validates: Requirements 16.2**
    
    For any verification result, the assigned classification should be one of the five
    valid categories: Fake, Misinformation, Bias, Misleading, or Verified.
    """
    # Act
    classification = get_classification(credibility_score, findings)
    
    # Assert
    assert classification in VALID_CLASSIFICATIONS, (
        f"Classification '{classification}' is not one of the valid categories. "
        f"Valid categories are: {VALID_CLASSIFICATIONS}"
    )
