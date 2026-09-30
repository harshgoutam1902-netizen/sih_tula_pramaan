# Complete API Endpoints Documentation

**Base URL**: `http://localhost:8000`  
**API Version**: v1  
**API Prefix**: `/api/v1`

---

## 📍 All Endpoints List

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/status` - API status with features

### Classification (5 endpoints)
- `POST /api/v1/classification/determine` - Determine class
- `POST /api/v1/classification/confirm` - Confirm classification
- `GET /api/v1/classification/suggest-min/{e}/{class}` - Get suggested Min
- `GET /api/v1/classification/history/{instrument_profile_id}` - Get history

### Instrument Profiles (5 endpoints)
- `POST /api/v1/instruments` - Create profile
- `GET /api/v1/instruments/{id}` - Get profile
- `PUT /api/v1/instruments/{id}` - Update profile
- `GET /api/v1/instruments` - List profiles
- `DELETE /api/v1/instruments/{id}` - Delete profile

### Test Plans (3 endpoints)
- `POST /api/v1/test-plans/assemble` - Assemble test plan
- `GET /api/v1/test-plans/{test_job_id}` - Get test plan
- `GET /api/v1/test-plans/{test_job_id}/summary` - Get summary

### Environment (5 endpoints)
- `POST /api/v1/environment/session` - Create session
- `GET /api/v1/environment/session/{test_job_id}` - Get session
- `POST /api/v1/environment/reading/override` - Override reading
- `GET /api/v1/environment/readings/{test_run_id}` - Get readings
- `GET /api/v1/environment/summary/{test_job_id}` - Get summary

### Development (DEBUG mode only)
- `POST /dev/reload-rulepacks` - Reload rulepacks

**Total Endpoints**: 23

---

## 🔐 Environment Variables

All endpoints can be configured via `.env` file:

```env
# Base URLs
API_BASE_URL=http://localhost:8000/api/v1
API_PREFIX=/api/v1

# Classification
CLASSIFICATION_DETERMINE_ENDPOINT=/api/v1/classification/determine
CLASSIFICATION_CONFIRM_ENDPOINT=/api/v1/classification/confirm
CLASSIFICATION_SUGGEST_MIN_ENDPOINT=/api/v1/classification/suggest-min/{e}/{class}
CLASSIFICATION_HISTORY_ENDPOINT=/api/v1/classification/history/{instrument_profile_id}

# Instruments
INSTRUMENT_PROFILE_CREATE_ENDPOINT=/api/v1/instruments
INSTRUMENT_PROFILE_GET_ENDPOINT=/api/v1/instruments/{id}
INSTRUMENT_PROFILE_UPDATE_ENDPOINT=/api/v1/instruments/{id}
INSTRUMENT_PROFILE_LIST_ENDPOINT=/api/v1/instruments
INSTRUMENT_PROFILE_DELETE_ENDPOINT=/api/v1/instruments/{id}

# Test Plans
TEST_PLAN_ASSEMBLE_ENDPOINT=/api/v1/test-plans/assemble
TEST_PLAN_GET_ENDPOINT=/api/v1/test-plans/{test_job_id}
TEST_PLAN_SUMMARY_ENDPOINT=/api/v1/test-plans/{test_job_id}/summary

# Environment
ENVIRONMENT_SESSION_ENDPOINT=/api/v1/environment/session
ENVIRONMENT_SESSION_GET_ENDPOINT=/api/v1/environment/session/{test_job_id}
ENVIRONMENT_READING_OVERRIDE_ENDPOINT=/api/v1/environment/reading/override
ENVIRONMENT_READINGS_GET_ENDPOINT=/api/v1/environment/readings/{test_run_id}
ENVIRONMENT_SUMMARY_ENDPOINT=/api/v1/environment/summary/{test_job_id}

# Health
HEALTH_ENDPOINT=/health
STATUS_ENDPOINT=/api/v1/status
ROOT_ENDPOINT=/
```

---

## 📊 Instrument Profile Endpoints (NEW)

### POST /api/v1/instruments
**Create Instrument Profile (Stage 1)**

**Request Body**:
```json
{
  "model_id": 100,
  "e": "0.001",
  "max_capacity": "150",
  "min_capacity": "0.020",
  "is_multi_range": false,
  "is_multi_interval": false,
  "sub_ranges": null,
  "self_indicating_type": "self_indicating",
  "indication_type": "digital",
  "is_electronic": true,
  "has_tare_device": true,
  "intended_use": "general_trade"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "model_id": 100,
  "e": "0.001",
  "max_capacity": "150",
  "min_capacity": "0.020",
  "is_multi_range": false,
  "is_multi_interval": false,
  "sub_ranges": null,
  "self_indicating_type": "self_indicating",
  "indication_type": "digital",
  "is_electronic": true,
  "has_tare_device": true,
  "intended_use": "general_trade",
  "created_at": "2026-09-28T10:30:00Z",
  "updated_at": null
}
```

---

### GET /api/v1/instruments/{id}
**Get Instrument Profile**

**Response** (200 OK):
```json
{
  "id": 1,
  "model_id": 100,
  "e": "0.001",
  "max_capacity": "150",
  "min_capacity": "0.020",
  "is_multi_range": false,
  "is_multi_interval": false,
  "sub_ranges": null,
  "self_indicating_type": "self_indicating",
  "indication_type": "digital",
  "is_electronic": true,
  "has_tare_device": true,
  "intended_use": "general_trade",
  "created_at": "2026-09-28T10:30:00Z",
  "updated_at": null
}
```

---

### PUT /api/v1/instruments/{id}
**Update Instrument Profile**

**Request Body** (partial update):
```json
{
  "min_capacity": "0.025",
  "has_tare_device": false
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "model_id": 100,
  "e": "0.001",
  "max_capacity": "150",
  "min_capacity": "0.025",
  "is_multi_range": false,
  "is_multi_interval": false,
  "sub_ranges": null,
  "self_indicating_type": "self_indicating",
  "indication_type": "digital",
  "is_electronic": true,
  "has_tare_device": false,
  "intended_use": "general_trade",
  "created_at": "2026-09-28T10:30:00Z",
  "updated_at": "2026-09-28T11:45:00Z"
}
```

---

### GET /api/v1/instruments
**List Instrument Profiles**

**Query Parameters**:
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Max records
- `model_id` (int, optional): Filter by model
- `is_electronic` (bool, optional): Filter by type

**Example**: `/api/v1/instruments?skip=0&limit=10&is_electronic=true`

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "model_id": 100,
    "e": "0.001",
    "max_capacity": "150",
    ...
  },
  {
    "id": 2,
    "model_id": 101,
    "e": "0.5",
    "max_capacity": "1.5",
    ...
  }
]
```

---

### DELETE /api/v1/instruments/{id}
**Delete Instrument Profile**

**⚠️ WARNING**: Cascades to delete all related classifications and test plans.

**Response** (204 No Content): Empty body

---

## 🔄 Complete Workflow Example

### Step 1: Create Instrument Profile

```bash
curl -X POST http://localhost:8000/api/v1/instruments \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 100,
    "e": "0.001",
    "max_capacity": "150",
    "min_capacity": "0.020",
    "is_multi_range": false,
    "is_multi_interval": false,
    "self_indicating_type": "self_indicating",
    "indication_type": "digital",
    "is_electronic": true,
    "has_tare_device": true,
    "intended_use": "general_trade"
  }'
```

Response: `{"id": 1, ...}`

### Step 2: Determine Classification

```bash
curl -X POST http://localhost:8000/api/v1/classification/determine \
  -H "Content-Type: application/json" \
  -d '{
    "e": "0.001",
    "max_capacity": "150",
    "rulepack_version": "R76-1:2006"
  }'
```

Response: `{"status": "DETERMINED", "class_": "II", ...}`

### Step 3: Confirm Classification

```bash
curl -X POST http://localhost:8000/api/v1/classification/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_profile_id": 1,
    "e": "0.001",
    "max_capacity": "150",
    "rulepack_version": "R76-1:2006",
    "status": "DETERMINED",
    "determined_class": "II",
    "computed_n": "150000.000000",
    "confirmed_by": 1
  }'
```

Response: `{"class_determination_id": 1, ...}`

### Step 4: Assemble Test Plan

```bash
curl -X POST http://localhost:8000/api/v1/test-plans/assemble \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_profile_id": 1,
    "class_determination_id": 1,
    "rulepack_version": "R76-1:2006"
  }'
```

Response: `{"test_plan_id": 1, "test_job_id": 101, "tests": [...], ...}`

### Step 5: Create Environment Session

```bash
curl -X POST http://localhost:8000/api/v1/environment/session \
  -H "Content-Type: application/json" \
  -d '{
    "test_job_id": 101,
    "start_temp": "23.2",
    "start_rel_h": "52",
    "start_time": "2026-09-28T09:30:00Z",
    "start_bar_pres": "1013.2"
  }'
```

Response: `{"environment_session_id": 1, ...}`

---

## 📝 Validation Rules

### Instrument Profile
- `e` > 0 (must be positive)
- `max_capacity` > 0
- `self_indicating_type`: one of `self_indicating`, `semi_self_indicating`, `non_self_indicating`
- `indication_type`: one of `digital`, `analogue` (required if `self_indicating_type` = `self_indicating`)
- `intended_use`: one of `general_trade`, `direct_sales`, `price_computing`, `labelling`, `grading`

### Classification
- `e` and `max_capacity` must be valid Decimal values
- `status`: one of `DETERMINED`, `AMBIGUOUS`, `INVALID`
- `override_reason` required if `status` = `AMBIGUOUS`

### Environment
- `checkpoint`: one of `start`, `max`, `end`
- `temp`: 10-40°C (warning if outside)
- `rel_h`: 20-90% (warning if outside)
- `bar_pres`: 900-1100 hPa (warning if outside)

---

## 🚨 Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes**:
- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request (validation error)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `422` - Unprocessable Entity (Pydantic validation)
- `500` - Internal Server Error

---

## 🧪 Testing Endpoints

### Using Swagger UI
```
http://localhost:8000/docs
```

### Using ReDoc
```
http://localhost:8000/redoc
```

### Using curl
See examples above for each endpoint.

### Using Python requests
```python
import requests

# Create instrument profile
response = requests.post(
    "http://localhost:8000/api/v1/instruments",
    json={
        "model_id": 100,
        "e": "0.001",
        "max_capacity": "150",
        # ... other fields
    }
)

profile = response.json()
print(f"Created profile: {profile['id']}")
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Setup Guide**: GETTING_STARTED.md
- **Architecture**: design.md
- **Task Breakdown**: tasks.md
