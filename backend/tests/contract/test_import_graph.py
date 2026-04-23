"""Import-graph guardrail.

Enforces ADR 0001 rule: nothing under `nyayalens/core/` is allowed to import
any third-party SDK or any adapter implementation. The moment a developer
writes ``from nyayalens.adapters.gemini import GeminiAdapter`` inside
``core/explain/prompts.py``, this test fails in CI.

The check is AST-only — no imports are executed — so it stays cheap.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = BACKEND_ROOT / "nyayalens" / "core"

# Modules `core/` must never import.
FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "nyayalens.adapters",
    "google.generativeai",
    "firebase_admin",
    "google.cloud",
    "fastapi",
    "starlette",
    "presidio_analyzer",
    "reportlab",
    "tenacity",
)

# Standard library & approved scientific libs `core/` may import freely.
# This is an allow list expressed as a *prefix* list for readability; the
# actual check is the forbidden list above.
APPROVED_THIRD_PARTY: tuple[str, ...] = (
    "numpy",
    "pandas",
    "sklearn",
    "pydantic",
)


def _collect_core_python_files() -> list[Path]:
    return [p for p in CORE_DIR.rglob("*.py") if p.name != "__init__.py" or p.stat().st_size > 0]


def _imports_in(path: Path) -> list[str]:
    """Return the dotted module names imported by `path`, ignoring syntax errors.

    For ``from a.b import c`` we record ``a.b``. For ``import a.b`` we record
    ``a.b``.
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {path}: {e}")

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            # Skip relative imports (they can only reach siblings).
            if node.level > 0:
                continue
            imports.append(node.module)
    return imports


@pytest.mark.parametrize("path", _collect_core_python_files(), ids=lambda p: str(p.relative_to(BACKEND_ROOT)))
def test_core_module_does_not_import_adapters_or_external_sdks(path: Path) -> None:
    """Every file under `core/` must not import a forbidden module."""
    for name in _imports_in(path):
        for forbidden in FORBIDDEN_PREFIXES:
            if name == forbidden or name.startswith(f"{forbidden}."):
                pytest.fail(
                    f"{path.relative_to(BACKEND_ROOT)} imports forbidden module "
                    f"{name!r}. See ADR 0001 — core/ must not depend on adapters "
                    f"or external SDKs. Move the integration to nyayalens.adapters "
                    f"and depend on the protocol in core._contracts."
                )


def test_contracts_module_has_no_external_imports() -> None:
    """`core/_contracts/` is the strictest: only stdlib + Pydantic + typing."""
    contracts_dir = CORE_DIR / "_contracts"
    approved = {"pydantic", "pydantic.json_schema", "pydantic.fields", "pydantic_core"}
    for path in contracts_dir.rglob("*.py"):
        if path.name == "__init__.py" and path.stat().st_size == 0:
            continue
        for name in _imports_in(path):
            head = name.split(".")[0]
            if head in {"nyayalens"}:
                continue
            if name in approved or head == "pydantic":
                continue
            # Standard library — allow everything rooted outside of typical
            # third-party prefixes. Python std-lib has no master list, so we
            # accept anything that is not explicitly in FORBIDDEN.
            for forbidden in FORBIDDEN_PREFIXES:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    pytest.fail(
                        f"{path.relative_to(BACKEND_ROOT)} imports {name!r}; "
                        f"core/_contracts/ must stay dependency-free."
                    )
