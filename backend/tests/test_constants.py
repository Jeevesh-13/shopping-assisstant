"""
Test constants integration
Verify that all constants are properly imported and used
"""
import pytest
from app.constants import (
    PROMPT_INJECTION_PATTERNS,
    SAFETY_MESSAGES,
    LLM_PROMPTS,
    CIRCUIT_BREAKER,
    RESPONSE_TEMPLATES
)


def test_safety_patterns_exist():
    """Test that safety patterns are defined"""
    assert len(PROMPT_INJECTION_PATTERNS) > 0
    assert all(isinstance(pattern, str) for pattern in PROMPT_INJECTION_PATTERNS)


def test_safety_messages_exist():
    """Test that safety messages are defined"""
    assert "adversarial" in SAFETY_MESSAGES
    assert "inappropriate" in SAFETY_MESSAGES
    assert "system_error" in SAFETY_MESSAGES
    assert all(isinstance(msg, str) for msg in SAFETY_MESSAGES.values())


def test_llm_prompts_exist():
    """Test that LLM prompts are defined"""
    assert "intent_classification" in LLM_PROMPTS
    assert "filter_extraction" in LLM_PROMPTS
    assert "response_generation" in LLM_PROMPTS
    assert all(isinstance(prompt, str) for prompt in LLM_PROMPTS.values())


def test_circuit_breaker_config():
    """Test circuit breaker configuration"""
    assert "failure_threshold" in CIRCUIT_BREAKER
    assert "timeout_seconds" in CIRCUIT_BREAKER
    assert isinstance(CIRCUIT_BREAKER["failure_threshold"], int)
    assert isinstance(CIRCUIT_BREAKER["timeout_seconds"], int)


def test_response_templates():
    """Test response templates"""
    assert "comparison_suggestions" in RESPONSE_TEMPLATES
    assert isinstance(RESPONSE_TEMPLATES["comparison_suggestions"], list)
    assert len(RESPONSE_TEMPLATES["comparison_suggestions"]) > 0


def test_constants_import_in_services():
    """Test that services can import constants"""
    from app.services.safety_service import SafetyService
    from app.services.llm_service import LLMService
    
    # These should not raise ImportError
    safety = SafetyService()
    assert safety is not None
    
    llm = LLMService()
    assert llm is not None
