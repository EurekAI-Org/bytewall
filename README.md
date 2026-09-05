# byteWall

A secure file upload service with asynchronous malware scanning, quarantine storage, and distributed background processing.

byteWall separates the public-facing API from file scanning and background jobs, allowing uploads to be processed without blocking incoming HTTP requests.

## Features

- Secure file upload handling
- File type and MIME validation
- Quarantine storage for untrusted uploads
- Asynchronous processing with Celery
- Malware scanning with ClamAV
- YARA rule scanning
- PostgreSQL-backed upload and scan state
- S3-compatible object storage
- Scheduled maintenance and retry jobs using Celery Beat
- Shared application code between API and workers

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
                  Validate + store metadata
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
             │    Celery    │
             │    Broker    │
             └──────┬───────┘
                    │
                    ▼
          ┌─────────────────────┐
          │   Celery Workers    │
          ├─────────────────────┤
          │ ClamAV              │
          │ YARA                │
          │ File processing     │
          │ Retry handling      │
          └──────────┬──────────┘
                     │
                     ▼
             ┌───────────────┐
             │  Scan Result  │
             └───────────────┘
```

Uploaded files are treated as untrusted and remain in quarantine until the required processing pipeline completes.

## Project Structure

```text
.
├── api/
│   ├── alembic/
│   ├── app/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
│
├── bg_workers/
│   ├── ...
│   ├── pyproject.toml
│   └── uv.lock
│
└── shared/
    └── src/
        └── shared/
```

### `api/`

Contains the FastAPI application.

Responsibilities include:

- Accepting file uploads
- Validating filenames
- Validating file extensions
- Detecting MIME types
- Enforcing upload size limits
- Writing upload metadata to PostgreSQL
- Storing files in quarantine
- Dispatching Celery tasks
- Exposing upload and processing status

### `bg_workers/`

Contains Celery workers and scheduled jobs.

Responsibilities include:

- ClamAV scanning
- YARA scanning
- File processing
- Updating scan results
- Retry handling
- Scheduled maintenance jobs

### `shared/`

Contains code shared by both the API and worker applications.

Examples include:

- Database models
- Database utilities
- Configuration
- Logging
- Constants
- Common types
- Shared schemas

## Requirements

The local development environment requires:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis or another Celery-compatible broker
- ClamAV
- S3-compatible object storage

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/lucifermorningstar1305/bytewall
cd byteWall
```

### 2. Install API dependencies

```bash
cd api
uv sync
```

### 3. Install worker dependencies

```bash
cd ../bg_workers
uv sync
```

---

## Running byteWall

For local development, run the API, Celery worker, and Celery Beat in separate terminals.

### API

```bash
cd api
uv run fastapi dev --port 8080
```

The API will be available at:

```text
http://localhost:8080
```

FastAPI Swagger documentation:

```text
http://localhost:8080/docs
```

---

### Celery Worker

```bash
cd bg_workers

uv run celery \
    -A celery_app:celery_app worker \
    -l INFO \
    -Q default,scan,beat \
    --concurrency 1 \
    --prefetch-multiplier=1 \
    -O fair
```

The worker currently listens to:

| Queue     | Purpose                               |
| --------- | ------------------------------------- |
| `default` | General background jobs               |
| `scan`    | File scanning and security processing |
| `beat`    | Tasks dispatched by scheduled jobs    |

### Celery Beat

```bash
cd bg_workers

uv run celery \
    -A celery_app:celery_app beat \
    -l INFO
```

Celery Beat is the scheduler.

It does not execute background jobs itself. Instead, it publishes scheduled tasks to Celery queues where workers consume them.

## Local Development

A typical local environment therefore has three application processes running:

```text
Terminal 1
FastAPI

Terminal 2
Celery Worker

Terminal 3
Celery Beat
```

The supporting infrastructure must also be available:

```text
PostgreSQL
Redis & RabbitMQ / Celery Broker
S3-compatible Storage
ClamAV
```

## File Processing Pipeline

```text
Upload
  │
  ▼
API Validation
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
  ├──► ClamAV Scan
  │
  ├──► YARA Scan
  │
  └──► Additional Processing
           │
           ▼
       Scan Result
```

A file may move through states such as:

```text
pending
   │
   ├──► clean
   │
   ├──► suspicious
   │
   ├──► malicious
   │
   └──► failed
```

Files should not be exposed to downstream applications while they are still considered untrusted.
