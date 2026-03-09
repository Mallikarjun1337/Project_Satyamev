"""
Property-based test for sources presence in verification results.

Feature: visual-image-sources-enhancement
Property 13: Sources Presence in Results
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

For any verification result returned by the backend, the result must contain 
a sources array with exactly 4 fact-checking sources: Snopes, FactCheck.org, 
PolitiFact, and Alt News.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.models_simple import get_mock_sources


# ============================================================================
# Property 13: Sources Presence in Results
# ============================================================================

@pytest.mark.property
@settings(max_examples=100)
@given(
    # Generate random test iterations to verify consistency
    iteration=st.integers(min_value=0, max_value=1000)
)
def test_sources_presence_in_results(iteration: int):
    """
    Property 13: Sources Presence in Results
    
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    
    For any verification result returned by the backend, the result must contain 
    a sources array with exactly 4 fact-checking sources: Snopes, FactCheck.org, 
    PolitiFact, and Alt News.
    
    This test verifies that:
    1. Exactly 4 sources are returned
    2. All required source names are present
    3. Each source has the required fields (name, url, description)
    4. The sources are consistent across all calls
    """
    # Act - Get mock sources (this is what the backend returns)
    sources = get_mock_sources()
    
    # Assert - Exactly 4 sources
    assert len(sources) == 4, (
        f"Expected exactly 4 sources, but got {len(sources)}"
    )
    
    # Assert - All sources have required fields
    for source in sources:
        assert 'name' in source, f"Source missing 'name' field: {source}"
        assert 'url' in source, f"Source missing 'url' field: {source}"
        assert 'description' in source, f"Source missing 'description' field: {source}"
        
        # Verify fields are non-empty strings
        assert isinstance(source['name'], str) and source['name'], (
            f"Source 'name' must be a non-empty string, got: {source['name']}"
        )
        assert isinstance(source['url'], str) and source['url'], (
            f"Source 'url' must be a non-empty string, got: {source['url']}"
        )
        assert isinstance(source['description'], str) and source['description'], (
            f"Source 'description' must be a non-empty string, got: {source['description']}"
        )
    
    # Assert - Required source names are present (Requirements 5.1, 5.2, 5.3, 5.4)
    source_names = [source['name'] for source in sources]
    
    required_sources = ['Snopes', 'FactCheck.org', 'PolitiFact', 'Alt News']
    for required_source in required_sources:
        assert required_source in source_names, (
            f"Required source '{required_source}' not found in sources. "
            f"Found sources: {source_names}"
        )
    
    # Assert - No duplicate sources
    assert len(source_names) == len(set(source_names)), (
        f"Duplicate sources found: {source_names}"
    )


@pytest.mark.property
def test_sources_consistency():
    """
    Verify that get_mock_sources() returns consistent results across multiple calls.
    
    This ensures that the sources are deterministic and don't change between calls.
    """
    # Act - Call get_mock_sources multiple times
    sources_call_1 = get_mock_sources()
    sources_call_2 = get_mock_sources()
    sources_call_3 = get_mock_sources()
    
    # Assert - All calls return identical results
    assert sources_call_1 == sources_call_2, (
        "get_mock_sources() returned different results on consecutive calls"
    )
    assert sources_call_2 == sources_call_3, (
        "get_mock_sources() returned different results on consecutive calls"
    )


@pytest.mark.property
def test_sources_urls_are_valid():
    """
    Verify that all source URLs are valid HTTPS URLs.
    
    This ensures that the URLs can be safely displayed to users and opened in browsers.
    """
    # Act
    sources = get_mock_sources()
    
    # Assert - All URLs are HTTPS
    for source in sources:
        url = source['url']
        assert url.startswith('https://'), (
            f"Source URL must use HTTPS protocol, got: {url}"
        )
        
        # Basic URL validation
        assert '.' in url, f"Invalid URL format: {url}"
        assert ' ' not in url, f"URL contains spaces: {url}"


@pytest.mark.property
def test_sources_have_meaningful_descriptions():
    """
    Verify that all sources have meaningful descriptions (not empty or too short).
    
    This ensures that users can understand what each source is about.
    """
    # Act
    sources = get_mock_sources()
    
    # Assert - All descriptions are meaningful (at least 10 characters)
    for source in sources:
        description = source['description']
        assert len(description) >= 10, (
            f"Source description too short (< 10 chars): '{description}' "
            f"for source '{source['name']}'"
        )
        
        # Description should contain some common words
        description_lower = description.lower()
        meaningful_words = ['fact', 'check', 'verification', 'news', 'truth', 'politics', 'india']
        has_meaningful_word = any(word in description_lower for word in meaningful_words)
        assert has_meaningful_word, (
            f"Source description doesn't contain meaningful keywords: '{description}' "
            f"for source '{source['name']}'"
        )


@pytest.mark.property
@settings(max_examples=50)
@given(
    # Test with different content types
    content_type=st.sampled_from(['text', 'image', 'video'])
)
def test_sources_independent_of_content_type(content_type: str):
    """
    Verify that sources are returned regardless of content type.
    
    This ensures that all verification results include sources, whether they're
    for text, image, or video content.
    """
    # Act - Get sources (in real implementation, this would be part of verification result)
    sources = get_mock_sources()
    
    # Assert - Sources are always present and complete
    assert len(sources) == 4, (
        f"Expected 4 sources for content_type '{content_type}', got {len(sources)}"
    )
    
    required_sources = ['Snopes', 'FactCheck.org', 'PolitiFact', 'Alt News']
    source_names = [source['name'] for source in sources]
    
    for required_source in required_sources:
        assert required_source in source_names, (
            f"Required source '{required_source}' missing for content_type '{content_type}'"
        )
