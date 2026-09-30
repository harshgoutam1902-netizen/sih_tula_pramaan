# API Endpoints Summary

## Base URL
```
http://localhost:8000
```

---

## Health & Status

### GET /
**Description**: Root endpoint with app info

**Response**:
```json
{
  "name": "TulaPramaan",
  "version": "1.0.0",
  "status": "running",
  "environment": "development"
}
```

### GET /health
**Description**: Health check for load balancers

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### GET /api/v1/status
**Description**: Detailed API status with feature flags

**Response**:
```json
{
  "status": "operational",
  "version": "1.0.0",
  "environment": "development",
  "features": {
    "ocr_enabled": true,
    "live_mpe_feedback": true,
    "multi_range_support": true,
    "batch_repetitive_tests": true,
    "environment_auto_propagation": true
  },
  "rulepack": {
    "default_version": "R76-1:2006",
    "cache_enabled": true
  }
}
```

---

## Classification Endpoints

### POST /api/v1/classification/determine
**Description**: Determine accuracy class from e and Max (Stage 1.5)

**Request**:
```json
{
  "e": "0.001",
  "max_capacity": "150",
  "rulepack_version": "R76-1:2006"
}
```

**Response**:
```json
{
  "status": "DETERMINED",
  "computed_n": "150000.000000",
  "class_": "II",
  "candidates": null,
  "reason": null,
  "suggested_min_capacity": "0.020"
}
```

**Possible Status Values**:
- `DETERMINED` - Single class match
- `AMBIGUOUS` - Multiple classes match (requires confirmation)
- `INVALID` - No class matches

---

### POST /api/v1/classification/confirm
**Description**: Confirm classification with human validation

**Request**:
```json
{
  "instrument_profile_id": 123,
  "e": "0.001",
  "max_capacity": "150",
  "rulepack_version": "R76-1:2006",
  "status": "DETERMINED",
  "determined_class": "II",
  "computed_n": "150000.000000",
  "override_reason": null,
  "confirmed_by": 45
}
```

**Response**:
```json
{
  "class_determination_id": 789,
  "message": "Classification confirmed successfully"
}
```

**Validation Rules**:
- `AMBIGUOUS` status requires `override_reason`
- `confirmed_by` must be valid user ID
- Only one confirmation per (instrument_profile_id, rulepack_version)

---

### GET /api/v1/classification/suggest-min/{e}/{accuracy_class}
**Description**: Get suggested Min capacity for given e and class

**Parameters**:
- `e` (path): Verification scale interval (e.g., "0.001")
- `accuracy_class` (path): One of I, II, III, IIII
- `rulepack_version` (query, optional): Default "R76-1:2006"

**Example**: `/api/v1/classification/suggest-min/0.001/II`

**Response**:
```json
{
  "e": "0.001",
  "accuracy_class": "II",
  "suggested_min_capacity": "0.020",
  "unit": "kg",
  "note": "Technician can override this value if needed"
}
```

---

### GET /api/v1/classification/history/{instrument_profile_id}
**Description**: Get classification history for an instrument

**Response**:
```json
[
  {
    "id": 789,
    "rulepack_version": "R76-1:2006",
    "computed_n": "150000.000000",
    "status": "DETERMINED",
    "determined_class": "II",
    "override_reason": null,
    "confirmed_by": 45,
    "confirmed_at": "2026-09-28T10:42:00Z",
    "created_at": "2026-09-28T10:42:00Z"
  }
]
```

---

## Test Plan Endpoints

### POST /api/v1/test-plans/assemble
**Description**: Assemble test plan from confirmed classification (Stage 2)

**Request**:
```json
{
  "instrument_profile_id": 123,
  "class_determination_id": 789,
  "rulepack_version": "R76-1:2006"
}
```

**Response**:
```json
{
  "test_plan_id": 456,
  "test_job_id": 101,
  "tests": [
    {
      "id": "1",
      "name": "Weighing performance",
      "clause_ref": "A.4.4 / A.5.3.1",
      "resolved_variant": null,
      "sequence": 1,
      "duration_category": "short"
    },
    {
      "id": "4.1",
      "name": "Discrimination",
      "clause_ref": "A.4.8",
      "resolved_variant": "digital",
      "sequence": 5,
      "duration_category": "short"
    }
    // ... more tests
  ],
  "class": "II",
  "total_count": 18,
  "summary": {
    "total_count": 18,
    "class": "II",
    "short_tests": 14,
    "time_spanning_tests": 4,
    "performance_tests": 10,
    "environmental_tests": 6,
    "checklist_tests": 2
  }
}
```

---

### GET /api/v1/test-plans/{test_job_id}
**Description**: Retrieve existing test plan

**Response**:
```json
{
  "id": 456,
  "test_job_id": 101,
  "rulepack_version": "R76-1:2006",
  "tests": [...],
  "class": "II",
  "total_count": 18,
  "created_at": "2026-09-28T09:30:00Z"
}
```

---

### GET /api/v1/test-plans/{test_job_id}/summary
**Description**: Get test plan summary statistics

**Response**:
```json
{
  "total_count": 18,
  "class": "II",
  "short_tests": 14,
  "time_spanning_tests": 4,
  "performance_tests": 10,
  "environmental_tests": 6,
  "checklist_tests": 2,
  "first_test": "Weighing performance",
  "last_test": "Checklist — electronic weighing instruments"
}
```

---

## Environment Endpoints

### POST /api/v1/environment/session
**Description**: Create environment session (Stage 3)

**Request**:
```json
{
  "test_job_id": 101,
  "start_temp": "23.2",
  "start_rel_h": "52",
  "start_time": "2026-09-28T09:30:00Z",
  "start_bar_pres": "1013.2"
}
```

**Response**:
```json
{
  "environment_session_id": 202,
  "message": "Environment session created successfully"
}
```

---

### GET /api/v1/environment/session/{test_job_id}
**Description**: Retrieve environment session

**Response**:
```json
{
  "id": 202,
  "test_job_id": 101,
  "start_temp": "23.2",
  "start_rel_h": "52",
  "start_time": "2026-09-28T09:30:00Z",
  "start_bar_pres": "1013.2",
  "created_at": "2026-09-28T09:30:00Z"
}
```

---

### POST /api/v1/environment/reading/override
**Description**: Override environment reading for specific checkpoint

**Request**:
```json
{
  "test_run_id": 567,
  "checkpoint": "end",
  "temp": "24.1",
  "rel_h": "55",
  "time": "2026-09-28T15:45:00Z",
  "bar_pres": "1012.8"
}
```

**Response**:
```json
{
  "environment_reading_id": 890,
  "source": "manual_override",
  "message": "Environment reading created"
}
```

**Valid Checkpoints**: `start`, `max`, `end`

---

### GET /api/v1/environment/readings/{test_run_id}
**Description**: Get all environment readings for a test run

**Response**:
```json
[
  {
    "id": 888,
    "test_run_id": 567,
    "checkpoint": "start",
    "temp": "23.2",
    "rel_h": "52",
    "time": "2026-09-28T09:30:00Z",
    "bar_pres": "1013.2",
    "source": "auto_carried",
    "created_at": "2026-09-28T09:30:00Z",
    "updated_at": null
  },
  {
    "id": 890,
    "test_run_id": 567,
    "checkpoint": "end",
    "temp": "24.1",
    "rel_h": "55",
    "time": "2026-09-28T15:45:00Z",
    "bar_pres": "1012.8",
    "source": "manual_override",
    "created_at": "2026-09-28T15:45:00Z",
    "updated_at": null
  }
]
```

---

### GET /api/v1/environment/summary/{test_job_id}
**Description**: Get consolidated environment summary (for final report)

**Response**:
```json
{
  "test_job_id": 101,
  "reading_count": 54,
  "temperature": {
    "min": 23.0,
    "max": 24.5,
    "avg": 23.7,
    "unit": "°C"
  },
  "relative_humidity": {
    "min": 50.0,
    "max": 56.0,
    "avg": 53.2,
    "unit": "%"
  },
  "barometric_pressure": {
    "min": 1011.8,
    "max": 1014.3,
    "avg": 1013.0,
    "unit": "hPa"
  },
  "note": "Consolidated from per-test records"
}
```

---

## Development Endpoints (DEBUG=true only)

### POST /dev/reload-rulepacks
**Description**: Reload all rulepacks (hot-reload for development)

**Response**:
```json
{
  "status": "success",
  "message": "Rulepacks reloaded"
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes**:
- `200` - OK
- `201` - Created
- `400` - Bad Request (validation error)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `500` - Internal Server Error

---

## Authentication

**Not yet implemented** - awaiting integration with existing auth system.

Future endpoints will require:
- Bearer token in `Authorization` header
- User ID for audit trail

---

## Interactive Documentation

Visit these URLs when server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide:
- Full endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Examples
