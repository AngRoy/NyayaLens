# NyayaLens backend — multi-stage Docker build for Cloud Run.
#
# Build:   gcloud builds submit --tag gcr.io/<project>/nyayalens-api ./backend
# Local:   docker build -t nyayalens-api ./backend
#          docker run -p 8000:8000 -e GEMINI_API_KEY=... nyayalens-api
#
# Cloud Run launches with $PORT (commonly 8080); we bind to it dynamically.

# ----- Builder stage ------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml ./
COPY nyayalens/__init__.py nyayalens/__init__.py

# Install runtime dependencies. Dev extras intentionally omitted.
RUN python -m pip install --upgrade pip && \
    pip install \
        "fastapi>=0.115,<0.200" \
        "uvicorn[standard]>=0.32,<0.40" \
        "python-multipart>=0.0.20" \
        "pydantic>=2.9,<3" \
        "pydantic-settings>=2.6,<3" \
        "numpy>=1.26,<3" \
        "pandas>=2.2,<3" \
        "scikit-learn>=1.5,<2" \
        "openpyxl>=3.1,<4" \
        "google-generativeai>=0.8,<1" \
        "firebase-admin>=6.5,<7" \
        "google-cloud-storage>=2.18,<3" \
        "presidio-analyzer>=2.2,<3" \
        "reportlab>=4.2,<5" \
        "tenacity>=9.0,<10"

# ----- Runtime stage ------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Non-root for Cloud Run hygiene.
RUN groupadd --system --gid 1001 nyayalens && \
    useradd  --system --uid 1001 --gid nyayalens --create-home nyayalens

WORKDIR /app

# Copy installed site-packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source.
COPY nyayalens ./nyayalens
COPY pyproject.toml ./

USER nyayalens

EXPOSE 8080

CMD ["sh", "-c", "uvicorn nyayalens.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
