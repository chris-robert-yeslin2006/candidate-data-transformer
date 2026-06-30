# Title: ADR-002 — Parser Registry Design

## Decision
Implement `ParserRegistry` as a plugin-style registry mapping `SourceType` to parser classes, with a `freeze()` mechanism that prevents modification after application startup. `ParserFactory` wraps the registry and provides automatic dependency injection (injecting `AiClient` into parsers that require it via `inspect.signature`).

## Why
- Registry decouples parser discovery from parser implementation — new parsers register themselves, the factory never changes.
- `freeze()` prevents accidental registration after configuration time, ensuring a deterministic parser set at runtime.
- Factory-level DI keeps parser constructors simple — they declare `ai_client` as a parameter and the factory supplies it.

## Alternatives Considered
- **Hard-coded if/else chain in factory** — rejected: violates Open/Closed principle; adding a new parser requires modifying the factory.
- **Entry-point based discovery (pkg_resources)** — rejected: over-engineered for the current scope; can be layered on top later.
- **Direct instantiation by callers** — rejected: couples callers to parser constructors; DI would be duplicated everywhere.

## Tradeoffs
- **Pro:** Adding a new source type requires only a parser class + one `registry.register()` call.
- **Pro:** Factory can `create_all()` to run all parsers concurrently on the same input.
- **Con:** Runtime introspection (`inspect.signature`) is fragile if constructor signatures change.
- **Con:** Frozen registry requires application restart for parser changes (acceptable for a service).

## Future Impact
- Every parser must declare `source_type` as a class attribute for registry dispatch.
- AI-dependent parsers (PDF, TXT) must accept `ai_client` in `__init__` for automatic injection.
- The registry could be extended to support Reader/Mapper composition for tabular formats (see Tech Debt Item #1).
