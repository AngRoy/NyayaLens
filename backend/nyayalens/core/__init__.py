"""Domain-agnostic NyayaLens engine.

Anything under `core/` MUST NOT import FastAPI, Firebase, Gemini, or any other
external SDK. See ADR 0001 for why, and `backend/tests/contract/test_import_graph.py`
for the enforcement.

Integration with external systems lives in `nyayalens.adapters`. Core talks to
adapters only through the protocols defined in `core._contracts`.
"""
