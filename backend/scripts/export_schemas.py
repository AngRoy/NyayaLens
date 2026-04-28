"""Export the public Pydantic DTOs in `nyayalens.models.api` as JSON Schema.

Used by the contract-test CI workflow (.github/workflows/contract-test.yml)
to detect API/Frontend DTO drift early. Each top-level DTO writes to
`shared/schemas/<ClassName>.json`; the Flutter side downloads the artifacts
and verifies its golden fixtures still parse.

Usage:
    python scripts/export_schemas.py --out ../shared/schemas
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from nyayalens.models import api as api_models

if TYPE_CHECKING:
    from pydantic import BaseModel

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "shared" / "schemas"


def _public_models() -> list[type["BaseModel"]]:
    """Discover the BaseModel subclasses re-exported by `nyayalens.models.api`."""
    from pydantic import BaseModel

    out: list[type[BaseModel]] = []
    for name in api_models.__all__:
        obj = getattr(api_models, name, None)
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            out.append(obj)
    return out


def export(out_dir: Path) -> list[Path]:
    """Write one JSON Schema file per public DTO. Returns the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for cls in _public_models():
        schema = cls.model_json_schema()
        path = out_dir / f"{cls.__name__}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    paths = export(args.out)
    print(f"Wrote {len(paths)} schema(s) to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
