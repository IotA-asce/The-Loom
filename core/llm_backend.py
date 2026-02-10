"""LLM Backend abstraction layer for The Loom.

Provides unified interface for multiple LLM providers (OpenAI, Anthropic, Ollama).
Supports streaming, retries, and fallback between providers.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Literal, Protocol


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM backend."""
    provider: LLMProvider
    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 60.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2000
    
    def __post_init__(self) -> None:
        if self.api_key is None and self.provider != LLMProvider.MOCK:
            # Try to load from environment
            env_key = self._get_env_key()
            if env_key:
                object.__setattr__(self, 'api_key', os.environ.get(env_key))
    
    def _get_env_key(self) -> str | None:
        """Get environment variable name for API key."""
        match self.provider:
            case LLMProvider.OPENAI:
                return "OPENAI_API_KEY"
            case LLMProvider.ANTHROPIC:
                return "ANTHROPIC_API_KEY"
            case LLMProvider.GEMINI:
                return "GEMINI_API_KEY"
            case _:
                return None


@dataclass(frozen=True)
class LLMMessage:
    """A message in the conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMRequest:
    """Request to LLM backend."""
    messages: tuple[LLMMessage, ...]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    
    def __post_init__(self) -> None:
        # Validate messages
        if not self.messages:
            raise ValueError("At least one message required")


@dataclass(frozen=True)
class LLMResponse:
    """Response from LLM backend."""
    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    
    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0) if self.usage else 0
    
    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0) if self.usage else 0
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0) if self.usage else 0


@dataclass(frozen=True)
class LLMStreamChunk:
    """A chunk of a streaming response."""
    content: str
    is_finished: bool = False
    finish_reason: str | None = None


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""
    
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate backend configuration."""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete response."""
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate a streaming response."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        pass


class MockLLMBackend(LLMBackend):
    """Mock backend for testing without API calls."""
    
    def _validate_config(self) -> None:
        pass
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return mock response."""
        user_message = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "No user message"
        )
        
        mock_content = f"""[Mock LLM Response]

Based on your prompt: "{user_message[:100]}..."

The story continues with faithful adherence to the established tone and character voices. The scene unfolds with tension that grips the air. Characters move through the space with purpose, their actions guided by underlying currents of narrative.

"We cannot turn back now," the voice rang out. The response came not in speech, but in the firmness of steps forward into uncertainty.

[End Mock Response]"""
        
        return LLMResponse(
            content=mock_content,
            model="mock-llm",
            usage={
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(mock_content.split()),
                "total_tokens": len(user_message.split()) + len(mock_content.split()),
            },
            finish_reason="stop"
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Yield mock streaming chunks."""
        import asyncio
        
        words = ["The", "story", "continues", "with", "faithful", "adherence", "..."]
        for word in words:
            await asyncio.sleep(0.05)  # Simulate delay
            yield LLMStreamChunk(content=word + " ", is_finished=False)
        
        yield LLMStreamChunk(content="", is_finished=True, finish_reason="stop")
    
    def count_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text.split())


class OpenAIBackend(LLMBackend):
    """OpenAI GPT backend."""
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        if self.config.provider != LLMProvider.OPENAI:
            raise ValueError(f"Expected OPENAI provider, got {self.config.provider}")
    
    def _get_client(self) -> Any:
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. Run: pip install openai"
                ) from e
            
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        return self._client
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate using OpenAI API."""
        client = self._get_client()
        
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=request.temperature or self.config.temperature,
            max_tokens=request.max_tokens or self.config.max_tokens,
            stream=False,
        )
        
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else None,
            finish_reason=choice.finish_reason,
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming using OpenAI API."""
        client = self._get_client()
        
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]
        
        stream = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=request.temperature or self.config.temperature,
            max_tokens=request.max_tokens or self.config.max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason
            
            if finish_reason:
                yield LLMStreamChunk(
                    content="",
                    is_finished=True,
                    finish_reason=finish_reason
                )
            elif delta.content:
                yield LLMStreamChunk(
                    content=delta.content,
                    is_finished=False
                )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to rough estimate
            return len(text.split()) * 4 // 3


class AnthropicBackend(LLMBackend):
    """Anthropic Claude backend."""
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        if self.config.provider != LLMProvider.ANTHROPIC:
            raise ValueError(f"Expected ANTHROPIC provider, got {self.config.provider}")
    
    def _get_client(self) -> Any:
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as e:
                raise ImportError(
                    "Anthropic package not installed. Run: pip install anthropic"
                ) from e
            
            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        return self._client
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate using Anthropic API."""
        client = self._get_client()
        
        # Separate system from messages
        system = None
        messages = []
        for m in request.messages:
            if m.role == "system":
                system = m.content
            else:
                messages.append({"role": m.role, "content": m.content})
        
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": request.temperature or self.config.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
        }
        if system:
            kwargs["system"] = system
        
        response = await client.messages.create(**kwargs)
        
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        
        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            } if response.usage else None,
            finish_reason=response.stop_reason,
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming using Anthropic API."""
        client = self._get_client()
        
        system = None
        messages = []
        for m in request.messages:
            if m.role == "system":
                system = m.content
            else:
                messages.append({"role": m.role, "content": m.content})
        
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": request.temperature or self.config.temperature,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "stream": True,
        }
        if system:
            kwargs["system"] = system
        
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield LLMStreamChunk(content=text, is_finished=False)
            
            final = await stream.get_final_message()
            yield LLMStreamChunk(
                content="",
                is_finished=True,
                finish_reason=final.stop_reason
            )
    
    def count_tokens(self, text: str) -> int:
        """Estimate tokens for Anthropic."""
        # Anthropic uses roughly 4 chars per token on average
        return len(text) // 4


class GeminiBackend(LLMBackend):
    """Google Gemini backend."""
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable.")
        if self.config.provider != LLMProvider.GEMINI:
            raise ValueError(f"Expected GEMINI provider, got {self.config.provider}")
    
    def _get_client(self) -> Any:
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
            except ImportError as e:
                raise ImportError(
                    "Google Generative AI package not installed. Run: pip install google-generativeai"
                ) from e
            
            genai.configure(api_key=self.config.api_key)
            self._client = genai
        
        return self._client
    
    def _convert_messages(self, messages: tuple[LLMMessage, ...]) -> tuple[str | None, str]:
        """Convert LLM messages to Gemini format.
        
        Gemini uses a different format:
        - System instruction is separate
        - Conversation is a single prompt with roles
        """
        system = None
        parts = []
        
        for m in messages:
            if m.role == "system":
                system = m.content
            elif m.role == "user":
                parts.append(f"User: {m.content}")
            elif m.role == "assistant":
                parts.append(f"Assistant: {m.content}")
        
        # Combine into single prompt (Gemini doesn't support multi-turn via generate_content)
        prompt = "\n\n".join(parts)
        return system, prompt
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate using Gemini API."""
        import asyncio
        
        client = self._get_client()
        
        # Convert messages
        system, prompt = self._convert_messages(request.messages)
        
        # Build generation config
        generation_config = {
            "temperature": request.temperature or self.config.temperature,
            "max_output_tokens": request.max_tokens or self.config.max_tokens,
        }
        
        # Create model
        model = client.GenerativeModel(
            model_name=self.config.model,
            system_instruction=system,
        )
        
        # Generate (run in executor since Gemini SDK is sync)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config=generation_config,
            )
        )
        
        # Extract content
        content = response.text if hasattr(response, 'text') else ""
        
        # Extract usage if available
        usage = None
        if hasattr(response, 'usage_metadata'):
            meta = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(meta, 'prompt_token_count', 0),
                "completion_tokens": getattr(meta, 'candidates_token_count', 0),
                "total_tokens": getattr(meta, 'total_token_count', 0),
            }
        
        return LLMResponse(
            content=content,
            model=self.config.model,
            usage=usage,
            finish_reason="stop" if response.candidates else "error",
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming using Gemini API."""
        import asyncio
        
        client = self._get_client()
        
        # Convert messages
        system, prompt = self._convert_messages(request.messages)
        
        generation_config = {
            "temperature": request.temperature or self.config.temperature,
            "max_output_tokens": request.max_tokens or self.config.max_tokens,
        }
        
        model = client.GenerativeModel(
            model_name=self.config.model,
            system_instruction=system,
        )
        
        # Generate streaming (run in executor)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True,
            )
        )
        
        # Yield chunks
        for chunk in response:
            if hasattr(chunk, 'text'):
                yield LLMStreamChunk(content=chunk.text, is_finished=False)
        
        yield LLMStreamChunk(content="", is_finished=True, finish_reason="stop")
    
    def count_tokens(self, text: str) -> int:
        """Estimate tokens for Gemini."""
        # Gemini uses roughly 4 chars per token on average
        return len(text) // 4


class OllamaBackend(LLMBackend):
    """Local Ollama backend for private inference."""
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None
    
    def _validate_config(self) -> None:
        if self.config.provider != LLMProvider.OLLAMA:
            raise ValueError(f"Expected OLLAMA provider, got {self.config.provider}")
    
    def _get_base_url(self) -> str:
        return self.config.base_url or self.DEFAULT_BASE_URL
    
    async def _request(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make request to Ollama API."""
        import aiohttp
        
        url = f"{self._get_base_url()}/api/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate using Ollama API."""
        # Combine messages into single prompt
        prompt_parts = []
        for m in request.messages:
            if m.role == "system":
                prompt_parts.append(f"System: {m.content}")
            elif m.role == "user":
                prompt_parts.append(f"User: {m.content}")
            else:
                prompt_parts.append(f"Assistant: {m.content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature or self.config.temperature,
                "num_predict": request.max_tokens or self.config.max_tokens,
            }
        }
        
        response = await self._request("generate", data)
        
        return LLMResponse(
            content=response.get("response", ""),
            model=self.config.model,
            usage=None,  # Ollama doesn't provide token counts
            finish_reason="stop" if not response.get("done_reason") else response.get("done_reason"),
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming using Ollama API."""
        import aiohttp
        
        prompt_parts = []
        for m in request.messages:
            if m.role == "system":
                prompt_parts.append(f"System: {m.content}")
            elif m.role == "user":
                prompt_parts.append(f"User: {m.content}")
            else:
                prompt_parts.append(f"Assistant: {m.content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": request.temperature or self.config.temperature,
                "num_predict": request.max_tokens or self.config.max_tokens,
            }
        }
        
        url = f"{self._get_base_url()}/api/generate"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                async for line in response.content:
                    if not line:
                        continue
                    import json
                    try:
                        chunk = json.loads(line)
                        yield LLMStreamChunk(
                            content=chunk.get("response", ""),
                            is_finished=chunk.get("done", False),
                            finish_reason="stop" if chunk.get("done") else None
                        )
                    except json.JSONDecodeError:
                        continue
    
    def count_tokens(self, text: str) -> int:
        """Rough token estimate for local models."""
        return len(text.split())


class LLMBackendFactory:
    """Factory for creating LLM backends."""
    
    _backends: dict[LLMProvider, type[LLMBackend]] = {
        LLMProvider.OPENAI: OpenAIBackend,
        LLMProvider.ANTHROPIC: AnthropicBackend,
        LLMProvider.GEMINI: GeminiBackend,
        LLMProvider.OLLAMA: OllamaBackend,
        LLMProvider.MOCK: MockLLMBackend,
    }
    
    @classmethod
    def create(cls, config: LLMConfig) -> LLMBackend:
        """Create backend from config."""
        backend_class = cls._backends.get(config.provider)
        if backend_class is None:
            raise ValueError(f"Unknown provider: {config.provider}")
        return backend_class(config)
    
    @classmethod
    def create_from_env(cls, provider: LLMProvider | None = None) -> LLMBackend:
        """Create backend from environment variables."""
        if provider is None:
            # Auto-detect from env
            if os.environ.get("OPENAI_API_KEY"):
                provider = LLMProvider.OPENAI
                model = os.environ.get("OPENAI_MODEL", "gpt-4")
            elif os.environ.get("ANTHROPIC_API_KEY"):
                provider = LLMProvider.ANTHROPIC
                model = os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            elif os.environ.get("GEMINI_API_KEY"):
                provider = LLMProvider.GEMINI
                model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
            elif os.environ.get("OLLAMA_MODEL"):
                provider = LLMProvider.OLLAMA
                model = os.environ.get("OLLAMA_MODEL", "llama2")
            else:
                provider = LLMProvider.MOCK
                model = "mock"
        else:
            model = {
                LLMProvider.OPENAI: os.environ.get("OPENAI_MODEL", "gpt-4"),
                LLMProvider.ANTHROPIC: os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                LLMProvider.GEMINI: os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
                LLMProvider.OLLAMA: os.environ.get("OLLAMA_MODEL", "llama2"),
                LLMProvider.MOCK: "mock",
            }[provider]
        
        config = LLMConfig(provider=provider, model=model)
        return cls.create(config)
    
    @classmethod
    def register_backend(
        cls,
        provider: LLMProvider,
        backend_class: type[LLMBackend]
    ) -> None:
        """Register a custom backend."""
        cls._backends[provider] = backend_class


class FallbackLLMBackend(LLMBackend):
    """Backend that falls back to secondary providers on failure."""
    
    def __init__(self, backends: list[LLMBackend]) -> None:
        if not backends:
            raise ValueError("At least one backend required")
        self.backends = backends
        self.config = backends[0].config  # Use primary config
    
    def _validate_config(self) -> None:
        pass
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Try backends in order until one succeeds."""
        last_error: Exception | None = None
        
        for backend in self.backends:
            try:
                return await backend.generate(request)
            except Exception as e:
                last_error = e
                continue
        
        raise last_error or RuntimeError("All backends failed")
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Try streaming from first working backend."""
        for backend in self.backends:
            try:
                async for chunk in backend.generate_stream(request):
                    yield chunk
                return
            except Exception:
                continue
        
        yield LLMStreamChunk(
            content="Error: All backends failed",
            is_finished=True,
            finish_reason="error"
        )
    
    def count_tokens(self, text: str) -> int:
        """Use primary backend's token counting."""
        return self.backends[0].count_tokens(text)


def get_available_providers() -> list[dict[str, Any]]:
    """Get list of available LLM providers based on environment."""
    providers = []
    
    # Check OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "available": True,
        })
    else:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "available": False,
            "reason": "OPENAI_API_KEY not set",
        })
    
    # Check Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append({
            "id": "anthropic",
            "name": "Anthropic",
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "available": True,
        })
    else:
        providers.append({
            "id": "anthropic",
            "name": "Anthropic",
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "available": False,
            "reason": "ANTHROPIC_API_KEY not set",
        })
    
    # Check Gemini
    if os.environ.get("GEMINI_API_KEY"):
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            "available": True,
        })
    else:
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            "available": False,
            "reason": "GEMINI_API_KEY not set",
        })
    
    # Check Ollama
    providers.append({
        "id": "ollama",
        "name": "Ollama (Local)",
        "models": ["llama2", "mistral", "codellama"],
        "available": True,  # Always available, may fail at runtime
        "note": "Requires Ollama running locally",
    })
    
    # Mock is always available
    providers.append({
        "id": "mock",
        "name": "Mock (Testing)",
        "models": ["mock"],
        "available": True,
    })
    
    return providers
