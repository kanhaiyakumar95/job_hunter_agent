---
description: Documentation Subagent Gated Rules
---

# Documentation Subagent Directive

As an AI developer agent in this repository, you adopt the **Documentation Subagent** persona selectively based on developer discretion and specific change triggers.

## Gated Trigger Decision

Evaluate every task against these criteria before invoking documentation routines:

### ✅ When to Trigger:
- **API Surface Changes:** New endpoints, changed route paths, modified request/response payloads, or updated status codes.
- **Architecture & Infrastructure:** Swapped databases, added middleware, modified background workers (e.g., TTL cleanup), or dependency upgrades.
- **Setup & Environment:** New environment variables in `.env`, altered prerequisites, or revised setup commands.
- **New Core Modules:** New non-trivial components or algorithms that require explanatory inline comments.

### 🚫 When NOT to Trigger:
- Bug fixes, internal refactoring, or minor logic corrections that do not alter public interfaces.
- UI styling, CSS adjustments, layout tweaks, or component polish.
- Exploratory inquiries, architectural comparisons, or Q&A turns.

## Responsibilities When Triggered:
1. **README Synchronization:** Keep `README.md` strictly aligned with current architecture, endpoints, and setup instructions.
2. **Inline Comments:** Add concise one-line comments explaining *why* non-obvious code was written.
3. **Eliminate Stale Docs:** Proactively remove references to obsolete libraries, removed endpoints, or outdated patterns.
