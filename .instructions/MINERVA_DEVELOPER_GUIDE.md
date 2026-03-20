# MINERVA Developer Onboarding & Integration Guide

Welcome to Minerva! This document provides technical details to help developers understand the architecture, integrate with the dashboard, and manage system behavior.

---

## 1. Project Onboarding Checklist

1.  **Clone & Setup Environment**:
    *   Initialize a Python 3.12+ virtual environment.
    *   `pip install -r requirements.txt`.
2.  **Database Initialisation**:
    *   Ensure a PostgreSQL instance is running.
    *   Apply base schemas (see `infra/db/`).
3.  **Local Storage**:
    *   Create a local directory for file storage (default: `/tmp/minerva_storage`).
4.  **Configuration**:
    *   Copy `.env.example` to `.env` and fill in provider API keys (e.g., `SARVAM_API_KEY`).
5.  **Run Services**:
    *   **Core API**: `uvicorn core.main:app --reload --port 8000`
    *   **Ingestion**: Triggered via `ingestion/main.py` (CLI or ECS task).

---

## 2. Configuration & System Controls

### 2.1 Environment Variables (`.env`)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `DB_HOST` | Database host address | `localhost` |
| `STORAGE_TYPE` | Storage backend: `local` or `s3` | `local` |
| `LOCAL_STORAGE_PATH` | Path for `local` storage type | `/tmp/minerva_storage` |
| `TENANT_SCHEMA` | Active schema for background tasks | `tenant_test` |
| `SARVAM_API_KEY` | API Key for Sarvam AI services | - |

### 2.2 Business Level Config (`business_configs` table)
Minerva is dynamic. Change provider configurations in the `public.business_configs` table to instantly change pipeline behavior for a specific business:
*   `stt_provider`: (e.g., `sarvam`, `deepgram`)
*   `llm_provider`: (e.g., `sarvam`, `openai`)
*   `tts_provider`: (e.g., `sarvam`, `elevenlabs`)
*   `rag_k_value`: Number of chunks to retrieve (default: `4`)

### 2.3 Feature Flags & Database Controls
*   **Document Versioning**: `documents.is_active` (bool). Only `true` documents are indexed for RAG.
*   **Session State**: `sessions.status` (`active`, `ended`).
*   **Job Tracking**: `ingestion_jobs.status` (`pending`, `processing`, `completed`, `failed`).

---

## 3. Data Layer: Repository Pattern

Minerva uses a **Repository Pattern** to abstract PostgreSQL logic and enforce tenant isolation.

### 3.1 Design Principles
1.  **Schema Context**: Repositories are instantiated with a `schema_name`.
2.  **Explicit Connections**: Use `get_connection(self.schema_name)` to automatically set the `search_path`.
3.  **Model Mapping**: Repositories return Pydantic/Dataclass models (e.g., `UsageRecord`) via the `.from_record()` class method.

### 3.2 Key Repositories
*   **`MessageRepository` (Core)**: CRUD for chat history and usage tracking (latency + consumption).
*   **`SessionRepository` (Core)**: Lifecycle management for conversation sessions.
*   **`IngestionRepository` (Ingestion)**: Handles document state, versioning (deactivation of old files), and job status updates.

---

## 4. API Reference (Internal & Core)

### 4.1 Internal Operations
| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/internal/health` | Service health and DB connection status. |
| `POST` | `/internal/cache/refresh` | Force global `ConfigCache` reload from DB. |
| `POST` | `/internal/cache/invalidate/{biz_id}` | Clear cache for specific tenant. |

### 4.2 Core Conversation Engine (`/api/v1/sessions`)
| Method | Route | Payload | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/` | - | `{"session_id": "...", "status": "active"}` |
| `POST` | `/{id}/message` | Multipart: `text`, `audio` (WAV), `language` | `{"response_text": "...", "latency_ms": {...}}` |

*Note: Dashboard integration should use standard multipart/form-data for message processing to support both voice and text inputs concurrently.*

---

## 5. Dashboard Integration Summary

To integrate the Minerva Dashboard with the Core engine:
1.  **Session Start**: Call `POST /api/v1/sessions/` to get a UUID.
2.  **Streaming Audio**: Upload audio segments to the message endpoint.
3.  **Usage UI**: Fetch metadata from the `tenant_<slug>.usage_records` table to show performance breakdowns.
4.  **Document Upload**: Upload knowledge base files to S3/Local storage and create a record in `documents` with `is_active = false` (Ingestion handles the rest).

---

## 6. Coding Standards Recap
*   **Multi-tenant Queries**: Never hardcode schemas. Use `get_connection`.
*   **Dynamic Metrics**: Usage units are stored in the `metrics` (JSONB) column of `usage_records`. Do not add new columns for specific units (e.g., image counts).
*   **Async/Await**: Ensure all DB and Provider interactions are awaited.
