"""
Parser registry and factory.

Implements a plugin-style architecture for parser discovery and
instantiation. New parsers are registered by source type and
created by the factory via dependency injection.

Adding a new parser requires:
  1. Create a new class inheriting from BaseParser
  2. Register it: ``registry.register(NewParser)``

No existing parser or pipeline code requires modification.

Future enhancements (deferred):
    - Plugin discovery via entry points or package scanning
    - Explicit dependency declarations instead of inspect.signature
      reflection (see _requires_ai_client)
"""

from __future__ import annotations

import logging
from typing import Any

from app.clients.base import AiClient
from app.domain.models.provenance import SourceType
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry mapping source type identifiers to parser classes.

    Acts as a plugin registry: new parsers register themselves
    with their source type, and the factory uses the registry
    to look up the correct parser for a given source.

    This class is the core of the Open/Closed design — adding
    a new source type requires registering a new parser class
    without modifying any existing registration code.

    The registry can be frozen after application startup to
    prevent runtime reconfiguration. Once frozen, register()
    raises RuntimeError.

    Future: Plugin packages (external parser modules) will be
    supported by allowing registration of parser classes from
    discoverable entry points. The registry is designed for
    this — register() is the sole extension point.

    Attributes:
        _parsers: Internal mapping of SourceType -> parser class.
        _frozen: Whether new registrations are prohibited.
    """

    def __init__(self) -> None:
        """Initialize an empty parser registry."""
        self._parsers: dict[SourceType, type[BaseParser]] = {}
        self._frozen: bool = False
        logger.debug("ParserRegistry created")

    def freeze(self) -> None:
        """
        Freeze the registry, preventing further registrations.

        Called after all built-in parsers are registered during
        application initialization. Ensures deterministic parser
        configuration for the lifetime of the application.
        """
        self._frozen = True
        logger.info(
            "ParserRegistry frozen with %d parsers", len(self._parsers)
        )

    @property
    def frozen(self) -> bool:
        """Whether the registry is frozen."""
        return self._frozen

    def register(self, parser_cls: type[BaseParser]) -> None:
        """
        Register a parser class by its source type.

        The parser class must define a ``source_type`` class attribute
        of type SourceType. Registration is idempotent — re-registering
        the same source type overwrites the previous entry with a warning.

        Args:
            parser_cls: The parser class to register.

        Raises:
            RuntimeError: If the registry is frozen.
            ValueError: If the parser class does not define source_type.
        """
        if self._frozen:
            raise RuntimeError(
                "Cannot register parser '%s': registry is frozen after startup"
                % parser_cls.__name__
            )

        source_type: SourceType | None = getattr(parser_cls, "source_type", None)
        if not source_type or not isinstance(source_type, SourceType):
            raise ValueError(
                f"{parser_cls.__name__} must define a 'source_type' "
                "class attribute of type SourceType"
            )

        if source_type in self._parsers:
            logger.warning(
                "Overwriting existing parser for source_type=%s", source_type
            )

        self._parsers[source_type] = parser_cls
        logger.debug(
            "Registered parser %s for source_type=%s",
            parser_cls.__name__,
            source_type,
        )

    def get(self, source_type: SourceType) -> type[BaseParser]:
        """
        Retrieve the parser class for a given source type.

        Args:
            source_type: The source type identifier.

        Returns:
            The registered parser class.

        Raises:
            KeyError: If no parser is registered for the source type.
        """
        if source_type not in self._parsers:
            raise KeyError(
                f"No parser registered for source_type='{source_type}'. "
                f"Available: {list(self._parsers.keys())}"
            )
        return self._parsers[source_type]

    def create(self, source_type: SourceType, **kwargs: Any) -> BaseParser:
        """
        Create a parser instance for the given source type.

        Any keyword arguments are forwarded to the parser's constructor,
        enabling dependency injection for parsers that require external
        dependencies (e.g., AiClient for AI-powered parsers).

        Args:
            source_type: The source type identifier.
            **kwargs: Dependencies to inject into the parser constructor.

        Returns:
            An instantiated parser.
        """
        parser_cls = self.get(source_type)
        logger.debug(
            "Creating %s with kwargs=%s",
            parser_cls.__name__,
            set(kwargs.keys()),
        )
        return parser_cls(**kwargs)

    @property
    def supported_types(self) -> list[SourceType]:
        """Return a list of all registered source types."""
        return list(self._parsers.keys())

    def __len__(self) -> int:
        """Return the number of registered parsers."""
        return len(self._parsers)


class ParserFactory:
    """
    Factory that creates parser instances with dependency injection.

    Wraps a ParserRegistry and manages shared dependencies that
    multiple parsers may need (e.g., AiClient). Callers ask for
    a parser by source type without needing to know each parser's
    specific constructor signature.

    The factory also provides convenience methods for batch
    operations like creating parsers for multiple source types.

    Dependency injection:
        Currently uses inspect.signature() to detect whether a
        parser requires ai_client. This is acceptable for the
        assignment. A future version should replace reflection
        with explicit dependency declarations (e.g., a class
        attribute listing required dependencies) or a lightweight
        DI container for better performance and clarity.

    Attributes:
        _registry: The underlying parser registry.
        _default_ai_client: Optional default AiClient for AI parsers.
    """

    def __init__(
        self,
        registry: ParserRegistry,
        default_ai_client: AiClient | None = None,
    ) -> None:
        """
        Initialize the parser factory.

        Args:
            registry: ParserRegistry instance with registered parsers.
            default_ai_client: Optional default AiClient to inject into
                               parsers that require one.
        """
        self._registry = registry
        self._default_ai_client = default_ai_client
        logger.debug(
            "ParserFactory created (ai_client=%s)",
            "provided" if default_ai_client else "none",
        )

    def create(self, source_type: SourceType, **overrides: Any) -> BaseParser:
        """
        Create a parser instance with automatic dependency injection.

        Automatically injects the default AiClient into parsers that
        require one, even if the client is None (the parser falls back
        to placeholder extraction). Callers can override any dependency
        via ``**overrides``.

        This explicit injection ensures parsers always receive their
        declared dependencies, making the system more robust when the
        AI client is unavailable (CLI mode, testing, etc.).

        Future: This method will also accept a ParserContext and
        forward relevant fields (ai_client, config) to the parser.

        Args:
            source_type: The source type to create a parser for.
            **overrides: Explicit dependency overrides for this call.

        Returns:
            An instantiated and configured parser.
        """
        parser_cls = self._registry.get(source_type)
        kwargs: dict[str, Any] = {}

        # Inject AiClient if the parser needs one (even if None)
        if _requires_ai_client(parser_cls):
            kwargs["ai_client"] = self._default_ai_client

        # Caller overrides take precedence
        kwargs.update(overrides)

        return self._registry.create(source_type, **kwargs)

    def create_all(self, source_types: list[SourceType]) -> dict[SourceType, BaseParser]:
        """
        Create parsers for multiple source types in one call.

        Args:
            source_types: List of source type identifiers.

        Returns:
            Dictionary mapping SourceType -> parser instance.
        """
        return {st: self.create(st) for st in source_types}

    @property
    def supported_types(self) -> list[SourceType]:
        """Return all supported source types from the registry."""
        return self._registry.supported_types


def _requires_ai_client(parser_cls: type[BaseParser]) -> bool:
    """
    Check if a parser class requires an AiClient.

    Inspects the constructor signature for an ``ai_client`` parameter.

    Note:
        This uses reflection (inspect.signature) which is fragile
        for subclass hierarchies. A future version should use
        explicit dependency declarations — e.g. a class attribute:
            required_dependencies = ["ai_client"]
        or a lightweight DI container with declared injection points.

    Args:
        parser_cls: The parser class to check.

    Returns:
        True if the parser requires ``ai_client``.
    """
    import inspect

    sig = inspect.signature(parser_cls.__init__)
    return "ai_client" in sig.parameters
