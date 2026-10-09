---
description: Low-Level Design (LLD) and Documentation Rules
---

# LLD Best Practices & Documentation Maintenance

As an AI agent working in this repository, you MUST adhere to the following Low-Level Design (LLD) and documentation practices:

## 1. Componentization & Modularity
- **Single Responsibility Principle:** Every class, function, or React component should have one primary responsibility.
- **Separate Concerns:** Keep UI logic separate from business logic. In React, move complex state or side-effects into custom hooks.
- **Small Files:** Extract large blocks of code (like list items or cards) into their own files/components.

## 2. Documentation Integrity
- **Always Keep Docs Updated:** Whenever you modify the architecture, API endpoints, or component structure, you MUST update the relevant documentation (e.g., README.md, architecture diagrams, or inline docstrings).
- **Self-Documenting Code:** Use descriptive variable and function names. Fall back to comments only for non-obvious logic or "why" explanations.

## 3. Asynchronous & Parallel Execution
- When appropriate, leverage parallel execution (like Promise.all in JS or asyncio.gather in Python) to improve performance.
- When performing independent tasks (like refactoring code vs updating docs), try to execute them concurrently if system tools allow.

## 4. Error Handling & Fallbacks
- Ensure all API calls have `try/catch` blocks.
- Provide graceful degradation in the UI (e.g., loading states, error boundaries, or mock fallbacks).
