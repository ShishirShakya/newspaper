# CONLAW Technical Constitution

**Version 1.0 — Python Scripts Edition**

## Purpose

This document defines the technical rules for the CONLAW project. The project consists of **Python scripts only** (automation, data, tooling), not a web application or long-running service. The goal is correctness, clarity, and maintainability without relying on any single person's memory or judgment.

**Status**: Living document  
**Audience**: All contributors  
**Scope**: Python scripts, config, dependencies, and project structure

---

## 0. Core Design Ethos

### Law 0.1 — Mechanized Trust Over Human Trust

**Scripts must be correct by construction, not by convention.**

Correctness enforced by: clear structure, narrow interfaces, explicit config, and simple control flow.

Correctness must not depend on: "remembering the rules," undocumented conventions, or "being careful."

**If a mistake is possible, it will happen.**

### Law 0.2 — Scripts, Not an App

- This project is **scripts only**. No backend server, no frontend, no API versioning, no deployment pipeline beyond running scripts.
- Scripts and shared modules live under `scripts/` (or a single documented project root).
- Each script has a clear purpose and a clear entrypoint (e.g. `if __name__ == "__main__"` or a single main module).
- Prefer small, focused scripts over one large "app." Compose with shared modules and config.

---

## 1. Architecture Principles (Scripts)

### 1.1 Configuration: Single Source of Truth

- **Environment and secrets**: Use `.env` and `python-dotenv` (or equivalent). No hardcoded credentials or URLs in code.
- **Project/config constants**: One canonical place (e.g. `scripts/newspapers_config.py` or a single `config` module). Other modules import from there; they do not redefine paths, URLs, or feature flags. Prefer one config module; if you introduce more (e.g. per-domain), document each module's name and responsibility.
- **Defaults**: Defaults live in that config module or in `.env.example`, not scattered across scripts.
- **Paths**: Resolve paths from the project root or from the config module (e.g. `PROJECT_ROOT`), not from the current working directory, so scripts behave the same when run from different directories.
- **Output naming**: Output filenames and paths come from config or from values defined in the config module; search parameters, result URLs, and screenshot/export naming are config, not literals in the middle of scripts.

### 1.2 No Hidden Global State or Side Effects on Import

- No module-level mutable state (e.g. global dicts, caches) that scripts depend on.
- No side effects on import: no network calls, no browser launch, no file writes when a module is imported. Side effects belong in explicit functions or in `if __name__ == "__main__"` blocks.
- Dependencies (e.g. Playwright page, browser context) are passed in or created in a clear entrypoint, not created at import time.

### 1.3 Minimalist Solution Principle

- No frameworks unless required for the task (e.g. Playwright for browser automation is required; avoid adding large app frameworks).
- Prefer the simplest correct implementation. Prefer standard library and a small set of dependencies.
- Each dependency should have a clear justification (see `pyproject.toml` and project docs).
- Long-running or network operations should use explicit timeouts (or documented defaults from config).

### 1.4 Shared Logic in One Place

- Reusable logic (e.g. browser context creation, login flow, navigation to results) lives in shared modules. Scripts call into them; they do not copy-paste the same logic.
- Constants (URLs, selectors, timeouts) defined once and imported. No duplicate string literals that represent the same concept.

---

## 2. Code Quality and Refactoring

### 2.1 Delete-First Refactoring

- Deprecated or unused code is removed, not commented out or left "for later."
- When changing behavior, remove old code paths and update callers. Prefer deletion over adding compatibility layers unless strictly necessary.

### 2.2 Net Code Reduction

- Prefer solutions that reduce total lines of code and duplication.
- New helpers or modules are justified by removing more code than they add, or by significantly improving clarity.

### 2.3 Error Handling

- Scripts fail loudly with clear messages. Avoid silent `except: pass` or swallowing errors without logging or re-raising.
- Best-effort steps (e.g. waiting for "networkidle") may catch and ignore errors only when the failure mode is documented and safe (e.g. script continues without that step).
- User-facing errors (e.g. "Login required") should be explicit. Use structured logging or print only where appropriate for a script context.

---

## 3. Anti-Patterns to Avoid

**Forbidden in scripts:**

- **Global mutable state**: No module-level dicts/lists/caches that are read or written by multiple callers without an explicit interface.
- **Side effects on import**: No config loading that touches the network, no browser launch, no file I/O at import time.
- **Scattered config**: No hardcoded URLs, paths, or credentials in the middle of scripts; use the config module and `.env`.
- **Duplicate definitions**: Same URL, same constant, or same selector defined in more than one file. Define once, import elsewhere.
- **Unclear entrypoints**: Scripts that run "everything" when imported. Use `if __name__ == "__main__"` or a single documented entrypoint so it is obvious how to run a script.
- **Import style**: Prefer top-level imports; use imports inside functions only when necessary (e.g. to avoid circular imports), and add a brief comment if the reason is not obvious.

**Enforcement:** Code review and optional lint/script checks. No automated gates are required by this constitution, but the rules above are mandatory for contributions.

---

## 4. Dependency and Environment

- **Dependencies**: Declared in `pyproject.toml` with version constraints. Use a single tool (e.g. `uv` or `pip`) for installs; document in README.
- **Secrets and env**: Document required env vars in `.env.example`. When a script gains a new env dependency, add it to `.env.example` with a short comment. Scripts read from environment or a small config layer that loads from env; never commit secrets.
- **Python version**: Pinned in `pyproject.toml` (e.g. `requires-python = ">=3.10"`). Scripts stay compatible with that range.

---

## 5. Testing and Execution

- **Testing**: Optional for scripts. If tests exist, they should be runnable via the project's standard command (e.g. `uv run pytest`).
- **Execution**: Scripts are run explicitly (e.g. `uv run python scripts/newspaper_screenshot.py`). Document the intended way to run each script in README or in docstrings.
- **Re-run behavior**: Scripts that write files should have clear, documented behavior on re-run (overwrite, append, or skip), e.g. in a docstring or README.

---

## 6. What This Constitution Does Not Cover

The following are **out of scope** for this script-only project:

- Frontend, TypeScript, or React
- Backend APIs, routers, services, or repositories
- State machines, locks, CAS, idempotency keys, or distributed systems
- API versioning, feature flags, or deployment pipelines
- WCAG, UI/UX laws, or accessibility standards for a UI
- On-call, incident response, or production SLAs

If the project later grows into an application, this document should be revised to include only the rules that apply to the new scope.

---

## 7. Constitutional Review Language

When reviewing changes, consider:

- "Where is the single source of truth for this config or constant?"
- "Does this introduce global state or side effects on import?"
- "Is this duplicate of an existing definition or helper?"
- "Can we delete this instead of adding a compatibility path?"
- "How do we run this script, and is that documented?"

---

## Final Rule

**If correctness depends on someone remembering the rules, the setup is incomplete.**  
Prefer explicit config, clear entrypoints, and minimal, obvious code.

---

## References

- **Project**: `pyproject.toml`, `.env.example`, README (if present)
- **Config**: `scripts/newspapers_config.py` (or equivalent single config module)
- **Document maintenance**: When editing this document, update Version and Last Updated.

---

**Last Updated**: 2025-03-09  
**Version**: 1.1 — Python Scripts Edition
