# LEARNING.md

Running notes from building DocIntel on top of SafeIntake. Updated each phase
with what we built, why this design over alternatives, the GCP services we
touched, and links to the official docs.

---

## Day 0: GCP services map

A 1-page mental model before you click anything in the console.

### The data flow we're building

```
        ┌─────────┐
upload  │ Cloud   │  PUT pdf          ┌────────────┐
PDF ───▶│ Run     ├──────────────────▶│   Cloud    │
        │ (API)   │  insert job row   │  Storage   │
        └────┬────┘─────┐             └────────────┘
             │          │
       publish msg      ▼
             │     ┌──────────┐
             │     │  Cloud   │
             │     │   SQL    │
             ▼     └──────────┘
        ┌─────────┐
        │ Pub/Sub │  fan out to workers
        └────┬────┘
             │
             ▼
        ┌─────────┐    call         ┌──────────────┐
        │ Cloud   ├────────────────▶│ Document AI  │  OCR + KV pairs
        │ Run     │                 └──────────────┘
        │ (worker)│
        │         │    call         ┌──────────────┐
        │         ├────────────────▶│ Vertex AI    │  classify + structure
        │         │                 │ (Gemini)     │
        │         │                 └──────────────┘
        │         │    write back   ┌──────────────┐
        │         ├────────────────▶│   Cloud SQL  │
        └─────────┘                 └──────────────┘
```

Reviewer UI (React) polls Cloud SQL via the API for results.

### The services, briefly

**Cloud Storage (GCS)** — buckets of files. Holds the uploaded PDFs and any
extracted artifacts. Equivalent to S3. Cloud Run is stateless, so anything
that needs to outlive a single request lives here.
Docs: https://cloud.google.com/storage/docs

**Cloud SQL** — managed Postgres. Stores the Document, Entity, and AuditEvent
rows. Equivalent to RDS Postgres. We use Cloud SQL instead of Neon for this
project so the entire stack is one cloud, which makes the portfolio story
cleaner.
Docs: https://cloud.google.com/sql/docs/postgres

**Cloud Run** — runs a container behind an HTTPS URL, scales to zero, no
servers to manage. Equivalent to AWS Fargate or App Runner. We'll deploy two
services: the public API and a Pub/Sub-triggered worker.
Docs: https://cloud.google.com/run/docs

**Pub/Sub** — a managed queue. One service publishes a message to a topic,
subscribers receive it and process. Equivalent to SNS + SQS combined, or a
lighter Kafka. We use it so the slow extraction work (10–60s per doc) runs
asynchronously and the upload HTTP request returns immediately.
Docs: https://cloud.google.com/pubsub/docs

**Document AI** — managed OCR plus structured extraction. Hand it a PDF, get
back text, key-value pairs, entities, and bounding boxes. There is a
specific Medical Records processor we'll use.
Docs: https://cloud.google.com/document-ai/docs

**Vertex AI (Gemini)** — Google's hosted LLM. We use it for the parts where
Document AI's pattern matching isn't enough: classifying the document type
and pulling structured fields out of narrative text. Gemini supports
structured output (give it a JSON schema, get back conforming JSON).
Docs: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview

**Secret Manager** — versioned storage for keys, passwords, connection
strings. Equivalent to AWS Secrets Manager. Cloud Run can mount secrets
directly as env vars, so the Cloud SQL password never lives in source.
Docs: https://cloud.google.com/secret-manager/docs

**IAM and service accounts** — a service account is a non-human identity
your services use to call other GCP APIs. Equivalent to AWS IAM roles. Cloud
Run needs to read GCS, query Cloud SQL, publish to Pub/Sub, call Document AI
and Vertex AI; the service account is what grants exactly those permissions.
Docs: https://cloud.google.com/iam/docs/service-accounts

**Cloud Logging** — every log line from every GCP service in one searchable
place. Equivalent to CloudWatch Logs. First place to look when something is
broken.
Docs: https://cloud.google.com/logging/docs

### Three-layer mental model

If you forget every service name, remember this much:

1. **Storage**: GCS for files, Cloud SQL for rows, Secret Manager for keys.
2. **Compute**: Cloud Run for everything that runs your code.
3. **AI**: Document AI for OCR and field extraction, Vertex AI for reasoning.

Glue: Pub/Sub for async, IAM for permissions, Cloud Logging for observability.

### Phase 0 checklist (what you do next, on your end)

Do these in the GCP console (https://console.cloud.google.com), one at a time.

1. **Create a project**
   - Top bar dropdown next to "Google Cloud" → "New Project".
   - Name: `safeintake-docintel`. Organization: leave default. Click Create.
   - Once created, select it from the same dropdown so all later actions land
     in this project.

2. **Enable billing**
   - Left nav → Billing. If you don't have a billing account, create one.
     New users get $300 in free credits that easily cover this project.
   - Link the billing account to `safeintake-docintel`.

3. **Enable the APIs we'll use**
   - Left nav → APIs & Services → Library. Search for and enable each:
     - Document AI API
     - Vertex AI API
     - Cloud Run Admin API
     - Cloud Pub/Sub API
     - Cloud Storage API
     - Cloud SQL Admin API
     - Secret Manager API
     - Cloud Build API (Cloud Run uses it for container builds)
   - You can also do this from a terminal once authenticated:
     ```
     gcloud services enable \
       documentai.googleapis.com \
       aiplatform.googleapis.com \
       run.googleapis.com \
       pubsub.googleapis.com \
       storage.googleapis.com \
       sqladmin.googleapis.com \
       secretmanager.googleapis.com \
       cloudbuild.googleapis.com
     ```

4. **Create a service account for local dev**
   - Left nav → IAM & Admin → Service Accounts → Create Service Account.
   - Name: `docintel-dev`. Description: "Local dev access to DocIntel
     resources".
   - Grant these roles (we'll tighten later): Storage Admin, Cloud SQL
     Client, Pub/Sub Publisher, Pub/Sub Subscriber, Document AI API User,
     Vertex AI User, Secret Manager Secret Accessor.
   - On the created account: Keys tab → Add Key → JSON. Download. Save it
     somewhere outside the repo (e.g., `~/.gcp/safeintake-docintel-dev.json`).
     This file is a credential, do not commit it.

5. **Wire up local auth**
   - Install the gcloud CLI if you don't have it:
     https://cloud.google.com/sdk/docs/install
   - Then run, in any terminal:
     ```
     gcloud auth login
     gcloud config set project safeintake-docintel
     gcloud auth application-default login
     export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp/safeintake-docintel-dev.json
     ```
     The third command lets local code find your credentials automatically.
     Add the export to your shell profile so it persists.

When that's done, ping me and we'll start **Phase 1: ingestion + storage**.
First code we'll write: a `services/intake/` FastAPI app with an upload
endpoint that writes the PDF to a GCS bucket and inserts a job row into Cloud
SQL.

### Notes on cost

The full project should sit comfortably inside the $300 free credit for a
new account. Rough monthly footprint if you leave everything idle:
- Cloud SQL: ~$10/mo for the smallest instance, unless we use a Cloud SQL
  micro tier ($7/mo) or stop the instance when not using it (free while
  stopped).
- Cloud Run: $0 when idle, fractions of a cent per request.
- Cloud Storage: pennies for the volumes we'll handle.
- Pub/Sub: free below 10GB/mo.
- Document AI: $1.50 per 1000 pages for the general processor; the medical
  one is more, but we'll be working with a tiny demo set.
- Vertex AI Gemini: a few dollars at most for the volumes we'll send.

Set a billing alert at $25 so nothing surprises you.

### What to ask me when we sync next

Things people commonly want a primer on at this stage:
- Why Pub/Sub instead of just calling Document AI directly from the API?
- What's the difference between Document AI and Vertex AI?
- Cloud Run vs Cloud Functions vs App Engine, when to use which?
- How do service-account credentials actually flow through to my code?

If any of those are fuzzy, flag it and I'll do the 5-minute primer when we
start Phase 1.
