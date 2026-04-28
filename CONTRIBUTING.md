# Contributing to NyayaLens

The full contributor guide lives at
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md). This file exists at
the repo root so GitHub's auto-discovery surfaces the guide on every
"New issue" / "New PR" page.

If you are about to open a PR, the headline rules are:

- `core/` is domain-agnostic. It must not import Firebase, Gemini, or
  FastAPI. The CI test `test_import_graph.py` enforces this.
- Raw strings never reach the LLM — only `LLMPayload` envelopes
  produced by the `PrivacyFilter`.
- Numbers in Gemini explanations must round-trip through the grounding
  validator. If the validator fails twice, we serve a templated
  fallback rather than a hallucinated number.
- `audit_trail/*` is append-only; signed-off audits are immutable.

Run `pytest`, `ruff check`, `ruff format --check`, and `mypy nyayalens`
in `backend/`, plus `flutter analyze` and `flutter test` in `frontend/`,
before pushing.

For everything else, please read the full guide.
