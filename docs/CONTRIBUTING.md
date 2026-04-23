# Contributing to NyayaLens

Welcome. NyayaLens is a small, high-accountability codebase. These rules exist
so the code stays coherent as the team grows.

## Ground rules

1. **`core/` is domain-agnostic.** It must never import Firebase, Gemini,
   FastAPI, or any other external SDK. A CI test enforces this.
2. **Raw strings never reach the LLM.** The `GeminiAdapter` accepts only
   `LLMPayload` envelopes. The `PrivacyFilter` is the sole constructor of
   those envelopes. Bypassing it is a type error.
3. **Numbers are not generated; they are injected.** Every Gemini explanation
   passes through the grounding validator. If a digit in the response is not
   in the injected metric values, the call is regenerated — and if that
   fails, we fall back to a templated explanation.
4. **Audit events are semantic, not HTTP-level.** Log an audit event at every
   decision point (tradeoff accepted, sign-off, schema confirmed, mitigation
   applied). Do not log every HTTP request as an audit event — that's
   observability, not accountability.
5. **Data provenance propagates.** Every Pydantic model that flows downstream
   carries the source (`real` / `benchmark` / `synthetic` / `llm_generated`).
   The PDF report cannot render without it.

## Before opening a PR

```sh
cd backend
ruff check .
ruff format --check .
mypy nyayalens
pytest

cd ../frontend
dart analyze
flutter test
```

All four must be green.

## Commit messages

Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
Reference the ADR or design-doc section when relevant
(e.g. `feat(bias): add DIR metric per design §7.2.2`).

## ADRs (Architecture Decision Records)

When you make a decision that changes a contract, a dependency direction,
or a protocol, write an ADR under `docs/adr/NNNN-short-slug.md`. Keep it
to one page: context, decision, consequences.

## Branch & merge

- Branch from `main` with `feature/<short-slug>` or `fix/<short-slug>`.
- Rebase before merge; prefer squash-merge.
- PRs need at least one review. For changes touching `core/_contracts/` or
  privacy code, two reviews.

## License

By contributing, you agree your contributions are licensed under Apache 2.0
(see `LICENSE`) and that the `NOTICE` file remains accurate.
