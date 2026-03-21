# Manual Testing Plan - Minerva

This document outlines the steps to manually verify the core functionalities of the Minerva platform, including the ingestion pipeline and the conversation engine.

## 1. Prerequisites & Setup

Ensure the following environment variables are set (local or dev environment):
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `STORAGE_TYPE` (local or s3)
- `LOCAL_STORAGE_PATH` (if using local storage)
- `SARVAM_API_KEY` (if testing with Sarvam provider)
- `PYTHONPATH=.`

---

## 2. Ingestion Pipeline Testing

### 2.1 Single Document Ingestion
**Goal**: Verify that a document can be processed, chunked, and indexed.

1.  **Prepare**: Place a PDF or text file in the storage location (e.g., `<LOCAL_STORAGE_PATH>/tenant_test/docs/kb_document.pdf`).
2.  **Trigger**: Manually trigger the ingestion job (or use the internal API/repository call).
3.  **Verify Status**:
    *   Check `tenant_test.ingestion_jobs` table. Status should transition from `pending` -> `processing` -> `completed`.
    *   Check `tenant_test.documents` table. `chunk_count` should be > 0 and `is_active` should be `true`.
4.  **Verify Output**:
    *   Ensure a `.faiss` and `.pkl` file are created in `<LOCAL_STORAGE_PATH>/tenant_test/index/`.

### 2.2 Versioning & Deactivation Logic
**Goal**: Verify that uploading a new version of the same file deactivates the old one.

1.  **Ingest Version 1**: Ingest `policy.pdf`. Verify it is `is_active = true`.
2.  **Ingest Version 2**: Create a new record for `policy.pdf` (different ID) and run ingestion.
3.  **Check DB**:
    *   Search `SELECT id, filename, is_active FROM tenant_test.documents WHERE filename = 'policy.pdf'`.
    *   **Success**: Only the latest ID should have `is_active = true`. The old one must be `false`.

---

## 3. Core Conversation Pipeline Testing

### 3.1 Session Management
1.  **Create Session**: Call `POST /api/v1/sessions/`.
2.  **Verify**:
    *   Check `tenant_test.sessions` table.
    *   **Critical**: Ensure the `business_id` column does NOT exist (or is NULL if not dropped) and the `status` is `active`.

### 3.2 Text-to-Audio (Response Generation)
1.  **Send Message**: Call `POST /api/v1/sessions/{id}/message` with text `{"text": "What is the policy coverage?", "language": "en-IN"}`.
2.  **Verify Response**:
    *   JSON should contain `response_text` and `response_audio_url`.
    *   `latency_ms` field should be present with sub-component timings.
3.  **Search Results**:
    *   Check `tenant_test.messages`. Ensure `rag_context` is populated with relevant document chunks.

### 3.3 Audio-to-Audio (STT + TTS)
1.  **Record**: Create a 5-second audio clip (WAV) asking a question.
2.  **Send Message**: Post the WAV file to `${id}/message`.
3.  **Verify**:
    *   `context.transcript` should match your spoken words.
    *   Response should be generated based on the knowledge base.

---

## 4. Analytics & Usage Verification

### 4.1 Dynamic Metrics
**Goal**: Verify consumption is tracked correctly in the JSON column.

1.  **Query DB**: `SELECT metrics, cost_estimate FROM tenant_test.usage_records ORDER BY created_on DESC LIMIT 1;`.
2.  **Success Criteria**:
    *   The `metrics` column (JSONB) should look like: `{"consumption": {"stt_seconds": 1.2, "llm_tokens": 150, "tts_characters": 45}}`.
    *   The `cost_estimate` column should be a float representing the estimated cost.

### 4.2 Latency Breakdown
1.  **Query DB**: `SELECT latency_ms FROM tenant_test.usage_records ...`.
2.  **Success Criteria**:
    *   Verify `stt`, `rag`, `llm`, and `tts` keys exist.
    *   Units should be in milliseconds (integers).

---

## 5. Error & Boundary Conditions

| Scenario | Expected Behavior |
| :--- | :--- |
| Corrupt PDF | Ingestion job status marked as `failed` with error message in DB. |
| Out of Scope Question | LLM should return "I don't know" or the pre-configured fallback. |
| Missing Audio in Voice Request | API returns 400 or falls back to text if provided. |
| Invalid Session ID | API returns 404 Not Found. |
| Expired Token / Missing Schema | API returns 401 Unauthorized or 403 Forbidden. |

---

## 6. Cleanup

To reset the test environment for a clean run:
```sql
TRUNCATE tenant_test.usage_records CASCADE;
TRUNCATE tenant_test.messages CASCADE;
TRUNCATE tenant_test.sessions CASCADE;
UPDATE tenant_test.documents SET is_active = false;
```
