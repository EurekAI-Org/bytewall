# byteWall

byteWall is a secure file upload service with asynchronous malware scanning, quarantine storage, file sanitization, and distributed background processing.

Uploaded files are treated as untrusted. Files are validated by the API, stored in quarantine, scanned asynchronously, sanitized where supported, scanned again, and only then moved to sanitized storage.

byteWall separates the public-facing API from the scanning pipeline so file processing does not block incoming HTTP requests.

---

## Features

- Secure file upload handling
- Filename validation
- File extension allowlisting
- Declared MIME type validation
- File signature / actual MIME type detection
- Upload size limits
- Quarantine storage for untrusted files
- Asynchronous processing with Celery
- Malware scanning with ClamAV
- Optional YARA rule scanning
- File sanitization
- Post-sanitization scanning
- PostgreSQL-backed upload and scan state
- S3-compatible object storage
- Redis-backed event publishing
- RabbitMQ-backed Celery task processing
- Scheduled maintenance and retry jobs with Celery Beat
- Separate API and worker containers

---

## Architecture

```text
                         ┌─────────────────┐
                         │     Client      │
                         └────────┬────────┘
                                  │
                                  │ Upload
                                  ▼
                         ┌─────────────────┐
                         │     FastAPI     │
                         │       API       │
                         └────────┬────────┘
                                  │
                          Validate upload
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌─────────────────┐          ┌─────────────────┐
          │   PostgreSQL    │          │   Quarantine    │
          │                 │          │     Storage     │
          └─────────────────┘          └─────────────────┘
                    │
                    │ Dispatch task
                    ▼
             ┌──────────────┐
             │   RabbitMQ   │
             │ Celery Broker│
             └──────┬───────┘
                    │
                    ▼
          ┌─────────────────────┐
          │   Celery Workers    │
          ├─────────────────────┤
          │ ClamAV              │
          │ YARA (optional)     │
          │ Sanitization        │
          │ Retry handling      │
          └──────────┬──────────┘
                     │
                     ▼
                Post Scan
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
           Reject        Sanitized
                           Storage
```

Uploaded files remain untrusted until the processing pipeline completes successfully.

---

## File Processing Pipeline

```text
Upload
  │
  ▼
API Validation
  │
  ├── Filename validation
  ├── Extension validation
  ├── Declared MIME validation
  ├── Actual MIME detection
  └── Size validation
  │
  ▼
Quarantine Storage
  │
  ▼
Database Record
  │
  ▼
Celery Task
  │
  ▼
Initial Scan
  │
  ├── ClamAV
  └── YARA (if configured)
  │
  ├──────────────► Malicious / Suspicious
  │
  ▼
Sanitization
  │
  ▼
Post-Sanitization Scan
  │
  ├── ClamAV
  └── YARA (if configured)
  │
  ▼
Sanitized Storage
```

Files that fail scanning or processing are not promoted to sanitized storage.

---

## Project Structure

```text
.
├── api/
│   ├── alembic/
│   ├── app/
│   │   ├── celery_modules/
│   │   ├── config/
│   │   ├── db/
│   │   ├── services/
│   │   ├── utility/
│   │   └── v1/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── uv.lock
│
├── bg_workers/
│   ├── rules/
│   ├── scanner/
│   ├── tasks/
│   ├── utility/
│   ├── celery_app.py
│   ├── celery_tasks.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── uv.lock
│
├── shared/
│   ├── src/
│   │   └── shared/
│   ├── pyproject.toml
│   └── uv.lock
│
├── compose.yaml
├── .env.example
├── LICENSE
└── README.md
```

### `api/`

Contains the FastAPI application.

Responsibilities include:

- Accepting file uploads
- Validating filenames
- Validating extensions
- Validating MIME types
- Detecting actual file types
- Enforcing file size limits
- Storing files in quarantine
- Writing upload metadata to PostgreSQL
- Dispatching background scan tasks

### `bg_workers/`

Contains the Celery workers and scheduled jobs.

Responsibilities include:

- Downloading quarantined files
- ClamAV scanning
- Optional YARA scanning
- File sanitization
- Post-sanitization scanning
- Uploading sanitized files
- Updating scan state
- Retry handling
- Cleanup
- Scheduled maintenance tasks

### `shared/`

Contains code shared between the API and background workers.

This includes:

- Database models
- Database tables
- Redis helpers
- Logging
- Shared types
- Celery queue definitions

---

# Docker Setup

The recommended way to run byteWall is with Docker Compose.

The provided Compose stack includes:

- byteWall API
- Celery default worker
- Celery scan worker
- Celery scheduled-task worker
- Celery Beat
- PostgreSQL
- Redis
- RabbitMQ
- ClamAV

An S3-compatible object storage service must be provided separately.

---

## Requirements

To run byteWall with Docker, you need:

- Docker
- Docker Compose
- Access to an S3-compatible object storage service

Examples of S3-compatible storage include AWS S3 and self-hosted S3-compatible services.

---

## 1. Clone the Repository

```bash
git clone https://github.com/<organisation>/bytewall.git
cd bytewall
```

---

## 2. Create the Environment File

Copy the provided example:

```bash
cp .env.example .env
```

Then update `.env` with the values for your environment.

Do not commit your `.env` file.

The repository contains `.env.example` only as a configuration reference.

---

## 3. Start byteWall

Run:

```bash
docker compose up -d
```

# API

The API is available by default at:

```text
http://localhost:8080
```

FastAPI Swagger documentation is available at:

```text
http://localhost:8080/docs
```

---

# YARA Rules

byteWall supports YARA as an optional additional scanning layer.

YARA rules are **not distributed with the public byteWall repository**.

The repository contains:

```text
bg_workers/
└── rules/
```

but does not ship a YARA ruleset.

This allows operators to use their own YARA rules without byteWall distributing private or organization-specific detection rules.

---

## Enabling YARA

byteWall looks for:

```text
bg_workers/rules/upload_rules_index.yar
```

during worker initialization.

If the file exists, byteWall compiles the YARA rules and enables YARA scanning.

If the file does not exist, YARA scanning is skipped and the remaining scanning pipeline continues normally.

---

## Example YARA Structure

You can organize your rules like this:

```text
bg_workers/
└── rules/
    ├── custom/
    │   ├── rule_one.yar
    │   └── rule_two.yar
    │
    └── upload_rules_index.yar
```

The index file may include individual rule files:

```yara
include "custom/rule_one.yar"
include "custom/rule_two.yar"
```

The rules and their organization are controlled by the operator running byteWall.

---

## Running Without YARA

YARA is optional.

If:

```text
bg_workers/rules/upload_rules_index.yar
```

does not exist, the worker skips YARA initialization.

The rest of the processing pipeline continues, including:

```text
ClamAV scanning
      │
      ▼
Sanitization
      │
      ▼
Post-sanitization scanning
```

---

# Manual Development

Docker Compose is the recommended way to run the complete stack.

For application development, the API and workers can also be run directly using Python and `uv`.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

The supporting infrastructure must still be available.

---

## Install API Dependencies

```bash
cd api
uv sync
```

Run the API:

```bash
uv run fastapi dev --port 8080
```

---

## Install Worker Dependencies

```bash
cd ../bg_workers
uv sync
```

Run a worker:

```bash
uv run celery \
    -A celery_app:celery_app worker \
    -l INFO \
    -Q default,scan,beat \
    --concurrency 1 \
    --prefetch-multiplier=1 \
    -O fair
```

Run Celery Beat:

```bash
uv run celery \
    -A celery_app:celery_app beat \
    -l INFO
```

---

# Security Model

byteWall assumes every uploaded file is untrusted.

The processing flow is designed around several basic principles:

- Validate before accepting an upload
- Store untrusted files separately
- Never expose quarantined files as trusted content
- Scan files before promotion
- Sanitize supported files
- Scan sanitized output again
- Keep processing asynchronous
- Fail rather than promote a file when required security processing cannot complete
- Keep runtime credentials outside container images

byteWall should be deployed behind appropriate authentication, authorization, TLS, and network controls for the environment in which it is used.

---

# License

byteWall is released under the MIT License.

See [`LICENSE`](LICENSE) for details.
