"""Protocols bridging `core/` to `adapters/`.

These are dependency-free. They import only from `typing`, Pydantic, and
other files in `_contracts/`. Anything else would let external SDK types
leak into the domain-agnostic engine.
"""
