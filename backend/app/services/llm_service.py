import asyncio
import time
from typing import Optional, Dict, Any, List
from enum import Enum
import json

import google.generativeai as genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings
from app.datamodels import QueryIntent, SearchFilters, ChatMessage
from app.constants import (
    LLM_PROMPTS,
    CIRCUIT_BREAKER,
    RETRY_CONFIG,
    MOCK_LLM_RESPONSE
)
from app.observability.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """LLM provider types."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker for LLM providers."""
    
    def __init__(self, failure_threshold: int = CIRCUIT_BREAKER["failure_threshold"], timeout: int = CIRCUIT_BREAKER["timeout_seconds"]):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        
        # HALF_OPEN state
        return True


class LLMService:
    """
    LLM service with multi-provider support and fallback mechanisms.
    """
    
    def __init__(self):
        self.providers: Dict[LLMProvider, Any] = {}
        self.circuit_breakers: Dict[LLMProvider, CircuitBreaker] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize LLM providers."""
        # Google Gemini (Primary)
        if settings.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                self.providers[LLMProvider.GEMINI] = genai.GenerativeModel(
                    settings.GEMINI_MODEL
                )
                self.circuit_breakers[LLMProvider.GEMINI] = CircuitBreaker()
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        
        # OpenAI (Fallback)
        if settings.OPENAI_API_KEY:
            try:
                self.providers[LLMProvider.OPENAI] = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY
                )
                self.circuit_breakers[LLMProvider.OPENAI] = CircuitBreaker()
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        # Anthropic (Secondary Fallback)
        if settings.ANTHROPIC_API_KEY:
            try:
                self.providers[LLMProvider.ANTHROPIC] = AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY
                )
                self.circuit_breakers[LLMProvider.ANTHROPIC] = CircuitBreaker()
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        if not self.providers:
            logger.warning("No LLM providers configured, using mock provider")
            self.providers[LLMProvider.MOCK] = None
            self.circuit_breakers[LLMProvider.MOCK] = CircuitBreaker()
    
    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate response with automatic fallback to other providers.
        """
        provider_order = [
            LLMProvider.GEMINI,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.MOCK
        ]
        
        last_error = None
        
        for provider in provider_order:
            if provider not in self.providers:
                continue
            
            circuit_breaker = self.circuit_breakers.get(provider)
            if circuit_breaker and not circuit_breaker.can_attempt():
                logger.warning(f"Circuit breaker open for {provider}, skipping")
                continue
            
            try:
                response = await self._generate_with_provider(
                    provider, prompt, system_prompt, temperature, max_tokens
                )
                
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                return response
                
            except Exception as e:
                last_error = e
                logger.error(f"Failed to generate with {provider}: {e}")
                
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                logger.error(f"LLM_ERROR | provider={provider.value} | error_type={type(e).__name__} | error={str(e)}")
                continue
        
        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def _generate_with_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate response with specific provider."""
        start_time = time.time()
        
        try:
            if provider == LLMProvider.GEMINI:
                response = await self._generate_gemini(
                    prompt, system_prompt, temperature, max_tokens
                )
            elif provider == LLMProvider.OPENAI:
                response = await self._generate_openai(
                    prompt, system_prompt, temperature, max_tokens
                )
            elif provider == LLMProvider.ANTHROPIC:
                response = await self._generate_anthropic(
                    prompt, system_prompt, temperature, max_tokens
                )
            else:  # MOCK
                response = await self._generate_mock(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Provider {provider} error: {e}")
            raise
    
    async def _generate_gemini(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Generate with Google Gemini."""
        model = self.providers[LLMProvider.GEMINI]
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        # Handle multi-part responses properly
        try:
            # Try simple text accessor first (most common case)
            return response.text
        except ValueError:
            # Response has multiple parts or safety issues
            if response.candidates:
                candidate = response.candidates[0]
                
                # Check if blocked by safety filters
                if candidate.finish_reason and candidate.finish_reason.name in ['SAFETY', 'RECITATION']:
                    logger.warning(f"Gemini response blocked: {candidate.finish_reason.name}")
                    raise Exception(f"Response blocked by safety filters: {candidate.finish_reason.name}")
                
                # Extract text from parts
                if candidate.content and candidate.content.parts:
                    text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                    if text_parts:
                        return ''.join(text_parts)
            
            # If we get here, something unexpected happened
            logger.error(f"Unexpected Gemini response structure: {response}")
            raise Exception("Unable to extract text from Gemini response")
    
    async def _generate_openai(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Generate with OpenAI."""
        client = self.providers[LLMProvider.OPENAI]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    async def _generate_anthropic(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> str:
        """Generate with Anthropic Claude."""
        client = self.providers[LLMProvider.ANTHROPIC]
        
        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_mock(self, prompt: str) -> str:
        """Mock provider for testing."""
        await asyncio.sleep(0.1)  # Simulate latency
        return json.dumps(MOCK_LLM_RESPONSE)
    
    async def classify_intent(self, query: str) -> QueryIntent:
        """Classify user query intent."""
        system_prompt = LLM_PROMPTS["intent_classification"]
        
        prompt = f"Query: {query}\n\nIntent:"
        
        try:
            response = await self.generate_with_fallback(
                prompt, system_prompt, temperature=0.3, max_tokens=50
            )
            intent_str = response.strip().lower()
            
            for intent in QueryIntent:
                if intent.value in intent_str:
                    return intent
            
            return QueryIntent.SEARCH
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return QueryIntent.SEARCH
    
    async def extract_filters(self, query: str) -> SearchFilters:
        """Extract search filters from user query."""
        system_prompt = LLM_PROMPTS["filter_extraction"]
        
        prompt = f"Query: {query}\n\nExtracted filters:"
        
        try:
            response = await self.generate_with_fallback(
                prompt, system_prompt, temperature=0.3, max_tokens=500
            )
            
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Remove markdown code block markers
                cleaned_response = cleaned_response.split("```")[1]
                if cleaned_response.startswith("json"):
                    cleaned_response = cleaned_response[4:]
                cleaned_response = cleaned_response.strip()
            
            # Parse JSON response
            filters_dict = json.loads(cleaned_response)
            return SearchFilters(**filters_dict)
            
        except json.JSONDecodeError as e:
            logger.error(f"Filter extraction failed - Invalid JSON: {e}. Response: {response[:100]}")
            return SearchFilters()
        except Exception as e:
            logger.error(f"Filter extraction failed: {e}")
            return SearchFilters()
    
    async def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """Generate natural language response."""
        system_prompt = LLM_PROMPTS["response_generation"]
        
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
        
        prompt = f"""Conversation History:
{history_text}

Context (Available Phones):
{context}

User Query: {query}

Response:"""
        
        return await self.generate_with_fallback(
            prompt, system_prompt, temperature=0.7, max_tokens=1024
        )


# Global instance
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return llm_service
