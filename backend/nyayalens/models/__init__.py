"""Pydantic models — TWO sub-packages.

`models.api`       — HTTP DTOs (versioned, stable; what the Flutter client sees)
`models.firestore` — Firestore document shapes (with nested maps, server timestamps)

Serializers between the two live in `adapters/firestore.py`. We never merge
the two. See ADR 0001 for rationale.
"""

# Pydantic 2 emits a deprecation-style UserWarning when a field is named
# `schema` (it shadows the now-deprecated BaseModel.schema() method). The
# wire field name is mandated by design doc §9.2 and renaming would force
# every Flutter DTO to drift. We suppress the cosmetic warning here.
import warnings as _warnings

_warnings.filterwarnings(
    "ignore",
    message=r'Field name "schema" in .* shadows an attribute in parent "BaseModel"',
    category=UserWarning,
    module=r"pydantic\..*",
)
