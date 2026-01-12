"""
Safety service for adversarial query detection and content moderation.
"""

import re
from typing import Tuple, Optional
from app.config import settings
from app.constants import (
    PROMPT_INJECTION_PATTERNS,
    API_KEY_EXTRACTION_PATTERNS,
    JAILBREAK_PATTERNS,
    TOXIC_PATTERNS,
    SAFETY_MESSAGES,
    SANITIZATION_PATTERNS
)
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SafetyService:
    """
    Safety service for detecting and blocking adversarial queries.
    """
    
    # Patterns loaded from constants
    PROMPT_INJECTION_PATTERNS = PROMPT_INJECTION_PATTERNS
    API_KEY_EXTRACTION_PATTERNS = API_KEY_EXTRACTION_PATTERNS
    JAILBREAK_PATTERNS = JAILBREAK_PATTERNS
    TOXIC_PATTERNS = TOXIC_PATTERNS
    
    def __init__(self):
        self.blocked_keywords = [kw.lower() for kw in settings.BLOCKED_KEYWORDS]
    
    def check_query_safety(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query is safe.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        if not settings.ENABLE_SAFETY_CHECKS:
            return True, None
        
        query_lower = query.lower()
        
        # Check length
        if len(query) > settings.MAX_QUERY_LENGTH:
            logger.warning(f"SAFETY | result=blocked | reason=query_too_long | length={len(query)}")
            return False, "Query too long"
        
        # Check for blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in query_lower:
                logger.warning(f"SAFETY | result=blocked | type=blocked_keyword | keyword={keyword}")
                return False, "Query contains blocked content"
        
        # Check for prompt injection
        if self._check_patterns(query_lower, self.PROMPT_INJECTION_PATTERNS):
            logger.warning("SAFETY | result=blocked | type=prompt_injection")
            return False, "Adversarial query detected"
        
        # Check for API key extraction
        if self._check_patterns(query_lower, self.API_KEY_EXTRACTION_PATTERNS):
            logger.warning("SAFETY | result=blocked | type=key_extraction")
            return False, "Adversarial query detected"
        
        # Check for jailbreak attempts
        if self._check_patterns(query_lower, self.JAILBREAK_PATTERNS):
            logger.warning("SAFETY | result=blocked | type=jailbreak")
            return False, "Adversarial query detected"
        
        # Check for toxic content
        if self._check_patterns(query_lower, self.TOXIC_PATTERNS):
            logger.warning("SAFETY | result=blocked | type=toxic_content")
            return False, "Inappropriate content detected"
        
        return True, None
    
    def _check_patterns(self, text: str, patterns: list) -> bool:
        """Check if text matches any pattern."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def sanitize_output(self, text: str) -> str:
        """Sanitize output to prevent information leakage."""
        # Remove any potential API keys or secrets
        text = re.sub(
            SANITIZATION_PATTERNS["api_keys"],
            '[REDACTED]',
            text
        )
        
        # Remove system-like prompts
        text = re.sub(
            SANITIZATION_PATTERNS["system_prompts"],
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        return text
    
    def get_safe_error_message(self, error_type: str) -> str:
        """Get safe error message for users."""
        return SAFETY_MESSAGES.get(error_type, SAFETY_MESSAGES["system_error"])


# Global instance
safety_service = SafetyService()


def get_safety_service() -> SafetyService:
    """Get safety service instance."""
    return safety_service
