# NyayaLens deploy aliases.
#
# These targets are thin wrappers around the PowerShell scripts under
# scripts/. On Windows you can also run the scripts directly:
#     ./scripts/deploy-backend.ps1
# On WSL / Linux / macOS, install pwsh and use these make targets.
#
# Override the project on the command line if you fork:
#     make deploy PROJECT=my-fork-project

PROJECT ?= nyayalens-28b93

.PHONY: help deploy-frontend deploy-backend deploy smoke logs-backend tests

help:
	@echo ""
	@echo "NyayaLens deploy targets:"
	@echo ""
	@echo "  make deploy-frontend   Rebuild + ship Flutter web to Firebase Hosting"
	@echo "  make deploy-backend    Rebuild + ship FastAPI to Cloud Run"
	@echo "  make deploy            Both, backend first"
	@echo "  make smoke             /health + Hosting + /api rewrite check"
	@echo "  make logs-backend      Tail last 50 Cloud Run logs"
	@echo "  make tests             flutter test + pytest (no deploy)"
	@echo ""
	@echo "Override the project: make deploy PROJECT=my-fork"
	@echo ""

deploy-frontend:
	pwsh ./scripts/deploy-frontend.ps1 -Project $(PROJECT)

deploy-backend:
	pwsh ./scripts/deploy-backend.ps1 -Project $(PROJECT)

deploy:
	pwsh ./scripts/deploy-all.ps1 -Project $(PROJECT)

smoke:
	pwsh ./scripts/smoke.ps1 -Project $(PROJECT)

logs-backend:
	pwsh ./scripts/logs-backend.ps1 -Project $(PROJECT)

tests:
	cd backend && pytest -q
	cd frontend && flutter test --no-pub
