"""NyayaLens — AI accountability operating system for hiring fairness."""

# Suppress Pydantic 2's UserWarning that fires when a field is literally
# named `schema` (it shadows the deprecated BaseModel.schema() helper).
# The wire field is mandated by design doc §9.2; renaming would cascade
# into Flutter DTOs. The field works correctly — only the warning is noise.
# This filter must be installed before any submodule with that field is
# imported, which is why it lives at the top-level package init.
import warnings as _warnings

_warnings.filterwarnings(
    "ignore",
    message=r'Field name "schema" in .* shadows an attribute in parent "BaseModel"',
    category=UserWarning,
)

__version__ = "0.1.0"
