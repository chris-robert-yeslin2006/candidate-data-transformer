# AI Assisted Development Workflow

AI was used as an engineering assistant during development. All generated code was reviewed, modified, tested, and understood before being committed.

---

## Usage Categories

### Architecture Review
AI was used to critique the proposed architecture before implementation began. Discussions focused on layer boundaries, dependency flow, and edge cases. The final architecture reflects decisions made collaboratively, not AI-generated output adopted verbatim.

### Project Scaffolding
AI generated initial project structure, configuration files (`pyproject.toml`, `ruff.toml`), and skeleton modules. This eliminated boilerplate setup time while maintaining full control over the structure.

### Library API Exploration
When integrating libraries (Pydantic, FastAPI, python-pptx), AI was used to quickly surface relevant API patterns and documentation. This is analogous to searching Stack Overflow or reading docs, but faster.

### Resume Extraction Prompt Refinement
The Gemini extraction prompt was developed iteratively with AI assistance. Each version was tested against sample resumes; the AI suggested improvements based on failure analysis. The final prompt is deterministic in its output structure, leaving no ambiguity for the parsing code.

### Test Case Generation
AI generated initial test cases for edge conditions (empty files, malformed data, missing fields, duplicate records). These were reviewed, adapted, and augmented with project-specific scenarios.

### Documentation Improvements
Drafts of project documentation were reviewed by AI for clarity, completeness, and consistency. All final text is written in the author's own words and reflects the author's understanding.

### Code Review
AI reviewed code for type errors, style violations, and potential bugs before human review. This is analogous to a linter or static analyser with conversational capabilities.

---

## Boundaries

| AI Role | Done | Not Done |
|---------|------|----------|
| Design Discussion | ✅ Explore alternatives | ❌ Design dictated by AI |
| Code Generation | ✅ Skeleton / boilerplate | ❌ Core business logic generated without review |
| Test Generation | ✅ Edge cases, parameterisation | ❌ Test assertions written without understanding |
| Debugging | ✅ Root cause suggestions | ❌ Blind copy-paste of fixes |
| Documentation | ✅ Review and suggest | ❌ Documentation written without verification |

---

## Verification Process

Every piece of AI-generated code passed through this checklist before commit:

1. **Read** — Understand what the code does at a statement level.
2. **Modify** — Adapt to project conventions; rename variables, adjust types, fix logic.
3. **Test** — Run existing and new tests; verify the behaviour with real inputs.
4. **Profile** — Ensure performance meets requirements.
5. **Own** — Be able to explain and defend every line in a code review.

---

## What Is NOT Saved

Raw ChatGPT transcripts, unmodified AI prompts, and AI-generated code that was not used are not stored in the repository. Only reviewed, modified, and understood artifacts are committed.
