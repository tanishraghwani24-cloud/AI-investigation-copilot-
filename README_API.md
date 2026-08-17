# AI Investigation Copilot API

Base URL for the backend is `http://127.0.0.1:8000`. Application routes are prefixed with `/api`.

Authentication is not implemented. All endpoints are unauthenticated.

## Common Error Envelope

All API errors use this JSON shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": []
  }
}
```

`error.code` is stable for client handling. `error.message` is human-readable. `error.details` is `null` unless field-level details are available.

Common status codes:

| Status | Code | Meaning |
| --- | --- | --- |
| `400` | `BAD_REQUEST` | Malformed request rejected by explicit API logic. |
| `404` | `NOT_FOUND` | Valid identifier, but the resource does not exist. |
| `409` | `CONFLICT` | Genuine resource conflict, if raised by an endpoint. |
| `422` | `VALIDATION_ERROR` | FastAPI/Pydantic validation failed for path, query, form, file, or JSON input. |
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected server failure. Details are not exposed to clients. |

Validation error example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["query", "limit"],
        "msg": "Input should be less than or equal to 100",
        "type": "less_than_equal",
        "ctx": {"le": 100}
      }
    ]
  }
}
```

Not found example:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Investigation not found: CASE-MISSING",
    "details": null
  }
}
```

Server error example:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected server error occurred",
    "details": null
  }
}
```

## Identifier Validation

Investigation path parameters named `case_id` must be 1-80 characters, start with an alphanumeric character, and contain only letters, numbers, `_`, or `-`.

Invalid path IDs return `422 VALIDATION_ERROR`. Valid but missing IDs return `404 NOT_FOUND`.

## Endpoints

### GET `/api/health`

Purpose: Verify that the API process is running.

Authentication: None.

Path parameters: None.

Query parameters: None.

Request body: None.

Successful response: `200 OK`

```json
{
  "status": "ok",
  "service": "ai-investigation-copilot"
}
```

Status codes: `200`, `500`.

Error responses: common error envelope.

Example request:

```bash
curl http://127.0.0.1:8000/api/health
```

### POST `/api/investigations`

Purpose: Create and persist a deterministic Mock Bank investigation case. The default seed is `42`; repeated requests for the same deterministic case are idempotent at the service layer.

Authentication: None.

Path parameters: None.

Query parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `scenario` | enum string | No | `default`, `high-risk`, `low-risk`, `missing-data` | Mock Bank scenario. Defaults to `default`. |

Request body: None.

Successful response: `200 OK`, an `InvestigationState`.

Status codes: `200`, `422`, `500`.

Error responses: invalid `scenario` returns `422 VALIDATION_ERROR`.

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/investigations?scenario=high-risk"
```

Example response:

```json
{
  "case_id": "CASE-2025-00042-HIGH-RISK",
  "case_input": {
    "transactions": [],
    "customer_profile": {"customer_id": "CUST-12345", "name": "Example Customer"},
    "merchant_info": null,
    "device_info": null,
    "beneficiary_info": null,
    "behavioral_biometrics": null,
    "face_verification": null,
    "supporting_documents": [],
    "alert_reason": "High-risk generated scenario"
  },
  "context_intelligence": null,
  "investigation_reasoning": null,
  "evidence_compliance_validation": null,
  "decision_optimization": null,
  "investigation_report": null,
  "current_stage": "INTAKE",
  "created_at": "2026-08-17T12:00:00Z",
  "updated_at": "2026-08-17T12:00:00Z",
  "errors": []
}
```

### GET `/api/investigations`

Purpose: List persisted investigations, optionally filtered by current pipeline stage.

Authentication: None.

Path parameters: None.

Query parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `status` | enum string | No | `INTAKE`, `CONTEXT`, `REASONING`, `COMPLIANCE`, `DECISION`, `REPORTING`, `DONE` | Current stage filter. |
| `offset` | integer | No | `>= 0`; default `0` | Number of records to skip. |
| `limit` | integer | No | `1` through `100`; default `20` | Maximum number of records returned. |

Request body: None.

Successful response: `200 OK`, an array of `InvestigationState`.

Status codes: `200`, `422`, `500`.

Error responses: invalid enum, negative offset, zero limit, or limit above `100` returns `422 VALIDATION_ERROR`.

Example request:

```bash
curl "http://127.0.0.1:8000/api/investigations?status=DONE&offset=0&limit=20"
```

Example response:

```json
[
  {
    "case_id": "CASE-2025-00042",
    "case_input": {
      "transactions": [],
      "customer_profile": null,
      "merchant_info": null,
      "device_info": null,
      "beneficiary_info": null,
      "behavioral_biometrics": null,
      "face_verification": null,
      "supporting_documents": [],
      "alert_reason": null
    },
    "context_intelligence": null,
    "investigation_reasoning": null,
    "evidence_compliance_validation": null,
    "decision_optimization": null,
    "investigation_report": null,
    "current_stage": "INTAKE",
    "created_at": "2026-08-17T12:00:00Z",
    "updated_at": "2026-08-17T12:00:00Z",
    "errors": []
  }
]
```

### GET `/api/investigations/{case_id}`

Purpose: Retrieve the current persisted state of one investigation. This is also the polling endpoint for asynchronous runs.

Authentication: None.

Path parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `case_id` | string | Yes | API identifier validation | Investigation case identifier. |

Query parameters: None.

Request body: None.

Successful response: `200 OK`, an `InvestigationState`.

Status codes: `200`, `404`, `422`, `500`.

Error responses: malformed `case_id` returns `422 VALIDATION_ERROR`; valid but missing case returns `404 NOT_FOUND`.

Example request:

```bash
curl http://127.0.0.1:8000/api/investigations/CASE-2025-00042
```

Example response:

```json
{
  "case_id": "CASE-2025-00042",
  "case_input": {
    "transactions": [],
    "customer_profile": null,
    "merchant_info": null,
    "device_info": null,
    "beneficiary_info": null,
    "behavioral_biometrics": null,
    "face_verification": null,
    "supporting_documents": [],
    "alert_reason": null
  },
  "context_intelligence": {"status": "IN_PROGRESS", "context_summary": null, "key_indicators": [], "anomalies": [], "risk_score": null},
  "investigation_reasoning": null,
  "evidence_compliance_validation": null,
  "decision_optimization": null,
  "investigation_report": null,
  "current_stage": "CONTEXT",
  "created_at": "2026-08-17T12:00:00Z",
  "updated_at": "2026-08-17T12:01:00Z",
  "errors": []
}
```

### POST `/api/investigations/{case_id}/run`

Purpose: Trigger asynchronous investigation execution for an existing persisted case. The endpoint returns immediately after marking work in progress.

Authentication: None.

Path parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `case_id` | string | Yes | API identifier validation | Investigation case identifier. |

Query parameters: None.

Request body: None.

Successful response: `202 Accepted`

```json
{
  "case_id": "CASE-2025-00042",
  "status": "IN_PROGRESS",
  "current_stage": "CONTEXT",
  "message": "Investigation execution started in the background. Poll this resource for progress."
}
```

Status codes: `202`, `404`, `422`, `500`.

Error responses: malformed `case_id` returns `422 VALIDATION_ERROR`; valid but missing case returns `404 NOT_FOUND`.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/investigations/CASE-2025-00042/run
```

## Asynchronous Investigation Flow

1. Create a case with `POST /api/investigations`.
2. Trigger execution with `POST /api/investigations/{case_id}/run`.
3. The trigger returns `202 Accepted` with `status: IN_PROGRESS` and the current stage.
4. Poll `GET /api/investigations/{case_id}` until `current_stage` reaches `DONE` or an agent output/error indicates failure.
5. If a run is already in progress, the trigger still returns `202 Accepted` and a message telling the client to poll the investigation resource.

There is no separate status endpoint in the current API.

### POST `/api/investigations/{case_id}/documents`

Purpose: Upload a supporting document for an investigation case.

Authentication: None.

Path parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `case_id` | string | Yes | API identifier validation | Investigation case identifier. |

Query parameters: None.

Request body: `multipart/form-data`

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `file` | file | Yes | Required by FastAPI | Uploaded document bytes. |
| `document_type` | string | No | 1-64 chars, letters/numbers/`_`/`-`; default `OTHER` | Client-provided type label such as `INVOICE`, `ID_SCAN`, or `BANK_STATEMENT`. |

Processing behavior: PDF files use text extraction first and OCR/Vision fallback for scanned PDFs. Image files with `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, or `.webp` use OCR/Vision. Other file extensions are stored with `processing_status: PENDING`.

Successful response: `200 OK`, a `SupportingDocument`.

Status codes: `200`, `404`, `422`, `500`.

Error responses: missing `file` or invalid `document_type` returns `422 VALIDATION_ERROR`; valid but unknown case returns `404 NOT_FOUND`.

Example request:

```bash
curl -X POST \
  -F "file=@statement.pdf" \
  -F "document_type=BANK_STATEMENT" \
  http://127.0.0.1:8000/api/investigations/CASE-2025-00042/documents
```

Example response:

```json
{
  "document_id": "DOC-1A2B3C4D",
  "document_type": "BANK_STATEMENT",
  "file_name": "statement.pdf",
  "file_url": "/path/to/backend/uploads/CASE-2025-00042/DOC-1A2B3C4D.pdf",
  "uploaded_at": "2026-08-17T12:00:00Z",
  "summary": "Extracted document preview",
  "extracted_text": "Full extracted text",
  "extracted_entities": [],
  "extracted_transactions": [],
  "evidence_references": [],
  "processing_status": "EXTRACTED"
}
```

### GET `/api/investigations/{case_id}/documents`

Purpose: List uploaded supporting documents for an investigation case.

Authentication: None.

Path parameters:

| Name | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `case_id` | string | Yes | API identifier validation | Investigation case identifier. |

Query parameters: None.

Request body: None.

Successful response: `200 OK`, an array of `SupportingDocument`.

Status codes: `200`, `404`, `422`, `500`.

Error responses: malformed `case_id` returns `422 VALIDATION_ERROR`; valid but unknown case returns `404 NOT_FOUND`.

Example request:

```bash
curl http://127.0.0.1:8000/api/investigations/CASE-2025-00042/documents
```

Example response:

```json
[
  {
    "document_id": "DOC-1A2B3C4D",
    "document_type": "BANK_STATEMENT",
    "file_name": "statement.pdf",
    "file_url": "/path/to/backend/uploads/CASE-2025-00042/DOC-1A2B3C4D.pdf",
    "uploaded_at": "2026-08-17T12:00:00Z",
    "summary": "Extracted document preview",
    "extracted_text": "Full extracted text",
    "extracted_entities": [],
    "extracted_transactions": [],
    "evidence_references": [],
    "processing_status": "EXTRACTED"
  }
]
```

## Generated Documentation Endpoints

These FastAPI-generated endpoints are also registered:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/openapi.json` | OpenAPI schema. |
| `GET` | `/docs` | Swagger UI. |
| `GET` | `/docs/oauth2-redirect` | Swagger UI OAuth redirect helper. Authentication is not implemented by this API. |
| `GET` | `/redoc` | ReDoc documentation UI. |
