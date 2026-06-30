# Title: ADR-003 — Parser Factory & Dependency Injection

## Decision
`ParserFactory` wraps a frozen `ParserRegistry` and is responsible for parser instantiation with automatic dependency injection. The factory inspects each parser's `__init__` signature via `inspect.signature` to determine whether it requires an `ai_client` parameter, injecting the configured `AiClient` implementation when needed.

## Why
- Separates parser construction from parser selection — the registry owns selection; the factory owns construction.
- Automatic DI means parsers don't need to know about the factory or the registry.
- The factory can be swapped or decorated (e.g., for caching or metrics) without touching parser code.

## Alternatives Considered
- **Parser implements a `configure()` method** — rejected: two-phase initialization is an anti-pattern.
- **Parser reads config globals directly** — rejected: couples parsers to environment; impossible to unit test without mocking os.environ.
- **Factory takes all possible dependencies as constructor args** — rejected: violates Interface Segregation; parsers that don't need AI still see ai_client.

## Tradeoffs
- **Pro:** Parsers declare their dependencies explicitly — the factory fulfills them.
- **Pro:** Unit tests can instantiate parsers directly without the factory, passing `MockGeminiClient` or `None` as needed.
- **Con:** Signature inspection adds a minor runtime cost per parser creation (negligible at service startup).
- **Con:** If a parser adds a new dependency parameter, the factory must be updated to supply it.

## Future Impact
- The factory's `create_all()` method enables parallel parsing across sources.
- Future dependencies (e.g., a caching layer, metrics client) would follow the same injection pattern.
- The factory could be extended to support constructor kwargs per parser configuration.
