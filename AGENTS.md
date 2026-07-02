# AGENTS.md

## Research, Verification, and Implementation Policy

Before implementing any solution, modification, upgrade, bug fix, integration, refactor, or architectural change, determine whether the task depends on software, services, libraries, frameworks, APIs, model formats, file formats, or platform behavior that may have changed since training.

For any work involving:

* AI models and tooling
* FLUX ecosystem
* ComfyUI
* LoRA training workflows
* fal.ai
* Cloudflare
* GitHub Actions
* Browser extensions
* Python packages
* JavaScript frameworks
* APIs and SDKs
* Build systems
* Deployment platforms
* Third-party repositories
* Open-source projects
* Operating system behavior
* Application configuration

Perform web research first.

### Research Requirements

* Use official documentation whenever available.
* Review release notes and changelogs for relevant software.
* Search repository documentation and active GitHub issues.
* Verify current implementation patterns before writing code.
* Prefer verified information over assumptions.

Do not assume:

* Current API behavior
* Current package versions
* Current configuration syntax
* Current platform limitations
* Current compatibility requirements
* Current file formats
* Current deployment procedures

### Debugging Requirements

When debugging:

* Search the exact error message.
* Search the exact stack trace when available.
* Search for known issues before proposing a fix.
* Review existing project code before introducing changes.
* Prefer documented solutions over speculative solutions.

### Implementation Requirements

Before making changes:

1. Inspect the existing codebase.
2. Understand the current architecture.
3. Identify how the requested change fits into the existing design.
4. Minimize unnecessary rewrites.
5. Preserve working functionality unless explicitly instructed otherwise.

When implementing:

* Follow current best practices supported by documentation.
* Avoid introducing unverified dependencies.
* Keep solutions maintainable and consistent with the existing project.
* Explain major implementation decisions in summaries or commit messages.

### Decision Order

Always follow this order:

1. Research
2. Verify
3. Inspect Existing Code
4. Plan
5. Implement
6. Test
7. Report Results

Never substitute confidence for verification.

The objective is not to produce code quickly.

The objective is to produce accurate, maintainable, verifiably correct solutions while minimizing correction cycles, regressions, technical debt, and unnecessary token usage.
