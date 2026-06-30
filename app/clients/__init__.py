"""External API clients (Gemini, OpenAI, HuggingFace, etc.)."""

from app.clients.base import AiClient
from app.clients.gemini import GeminiClient, MockGeminiClient

__all__ = ["AiClient", "GeminiClient", "MockGeminiClient"]
