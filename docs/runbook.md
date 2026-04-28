# NyayaLens — Production Runbook

This runbook covers the deploy path from a clean GCP project to a
publicly-reachable Cloud Run URL plus the Firebase Hosting frontend.
The MVP runs entirely on free-tier resources unless you put the
backend behind a load balancer; cost notes below are ballpark, not
committed.

## 1. One-time GCP bootstrap

```sh
# 1. Create / select the project.
gcloud projects create nyayalens --name="NyayaLens"
gcloud config set project nyayalens

# 2. Enable the APIs the deploy pipeline touches.
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  firebasehosting.googleapis.com

# 3. Create the runtime service account.
gcloud iam service-accounts create nyayalens-api \
  --display-name="NyayaLens API runtime"

# 4. Grant it Firestore + Storage access.
SA=nyayalens-api@nyayalens.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding nyayalens \
  --member="serviceAccount:${SA}" \
  --role="roles/datastore.user"
gcloud projects add-iam-policy-binding nyayalens \
  --member="serviceAccount:${SA}" \
  --role="roles/storage.objectAdmin"
```

## 2. Secrets

The Gemini API key is the only secret the runtime container needs.
Store it in Secret Manager; `infra/cloud-run/service.yaml` already
wires it via `secretKeyRef`.

```sh
echo -n "<your-gemini-api-key>" | gcloud secrets create gemini-api-key \
  --replication-policy=automatic --data-file=-

# Allow the runtime service account to read it.
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"
```

## 3. Environment variable matrix

| Variable | Where | Required in prod? | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | Secret Manager → injected by service.yaml | yes | falls back to MockLLMClient in dev |
| `NYAYALENS_ENV` | service.yaml env block | yes (`prod`) | controls auth strictness, hides /docs |
| `GOOGLE_CLOUD_PROJECT` | service.yaml env block | yes | Firebase Admin auto-detects from this |
| `FIREBASE_STORAGE_BUCKET` | service.yaml env block | yes | typically `<project>.appspot.com` |
| `CORS_ALLOWED_ORIGINS` | service.yaml env block | yes | comma-separated list including the Firebase Hosting URL |
| `GEMINI_MODEL_EXPLAIN` / `GEMINI_MODEL_SCHEMA` | service.yaml | no | sensible defaults (`gemini-flash-latest` / `gemini-pro-latest`) |
| `GEMINI_TEMPERATURE` | service.yaml | no | default `0.2`, lock for grounding |
| `SCHEMA_DETECTION_LLM_TIMEOUT_SECONDS` | service.yaml | no | default `20.0` |
| `ENABLE_RESPONSE_CACHE` / `ENABLE_GROUNDING_VALIDATOR` | service.yaml | no | both default `true`; do not disable in prod |
| `FIRESTORE_EMULATOR_HOST` / `FIREBASE_AUTH_EMULATOR_HOST` / `FIREBASE_STORAGE_EMULATOR_HOST` | local dev only | no | `firebase emulators:start` sets these for child processes |

## 4. First deploy

The Cloud Build pipeline at `infra/cloud-run/cloudbuild.yaml` builds
the image, pushes to GCR with the commit SHA + `latest` tags, then
substitutes `${IMAGE}` into `infra/cloud-run/service.yaml` via
`envsubst` and applies the manifest. SHA-pinning means rollbacks are
addressable by commit hash.

```sh
# Manual one-shot from a clean checkout.
gcloud builds submit --config infra/cloud-run/cloudbuild.yaml ./backend
```

Or wire to a GitHub trigger that fires on push-to-main; the same
config works for both modes.

## 5. Frontend (Firebase Hosting)

```sh
cd frontend
flutter build web --release \
  --dart-define=API_BASE=https://nyayalens-api-xxxxx.run.app/api/v1
firebase deploy --only hosting
```

The `infra/firebase.json` rewrite already maps `/api/**` to the Cloud
Run service so cross-origin headaches stay minimal.

## 6. Firestore rules

```sh
firebase deploy --only firestore:rules,storage:rules
```

`shared/firestore.rules` enforces:

- Org-scoped reads on every collection.
- `audit_trail/*` is service-account-only on the create side; clients
  cannot forge events.
- Once an audit's `status == "signed_off"`, no client (including
  admins) can modify the doc — corrections happen via a new
  `audit_trail` event with `details.reason`.

## 7. Smoke test (run before walking away from a deploy)

```sh
BASE_URL=https://nyayalens-api-xxxxx.run.app
curl -sf "$BASE_URL/health" | jq .
# expect: {"status":"ok","version":"...","env":"prod","emulators":"off"}

# Upload the seeded synthetic CSV.
curl -sf -X POST "$BASE_URL/api/v1/datasets/upload" \
  -H "X-User-Id: smoke" -H "X-User-Role: admin" -H "X-Organization-Id: smoke-org" \
  -F "domain=hiring" \
  -F "file=@shared/sample_data/placement_synthetic.csv" | jq '.row_count, .quality.overall_score'
# expect: 600 and a number in [0, 1]
```

If `NYAYALENS_ENV=prod` is set, the demo `X-User-*` headers will be
rejected; in production every request needs a valid Firebase ID token
in `Authorization: Bearer <jwt>`.

## 8. Rollback

```sh
# List recent revisions.
gcloud run revisions list --service=nyayalens-api --region=asia-south1

# Roll traffic back to a known-good revision.
gcloud run services update-traffic nyayalens-api \
  --region=asia-south1 \
  --to-revisions=<revision-name>=100
```

Because every revision is image-pinned by SHA, this is fast.

## 9. Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| 403 on every API call | demo headers used in prod | switch the client to ID-token auth |
| 502 on schema detection | Gemini key missing or invalid | verify Secret Manager binding + IAM |
| `audit_trail` writes silently dropped | client trying to write directly | route through the backend; the rule blocks client creates |
| Reports take >20 s | cold start + ReportLab boot | bump Cloud Run min-instances to 1 |
| CORS errors in browser | Hosting URL not in `CORS_ALLOWED_ORIGINS` | add it and redeploy the Cloud Run service |
| 409 on a /audits/{id}/* call | the record is `mode=probe` | use `/probes/*` endpoints for probe records |

## 10. Post-deploy checklist

- [ ] `/health` returns 200.
- [ ] `/docs` is hidden in prod (`is_production=True` disables it).
- [ ] Secret Manager binding for `gemini-api-key` is `latest`.
- [ ] Cloud Run min-instances is `0` (cost) or `1` (latency) per environment.
- [ ] Firestore rules and Storage rules have been deployed alongside the backend.
- [ ] Frontend `--dart-define=API_BASE=...` matches the Cloud Run URL.
- [ ] `firebase emulators:start` is no longer running on the dev machine (it leaks env vars to local processes).
