# Design Document: 3-Stage Smart Form System
### TulaPramaan — OIML R 76 Type Evaluation & Test Report Automation

## 1. Architecture Overview

### 1.1 System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Stage 1 UI  │→ │ Stage 1.5 UI │→ │  Stage 2 UI  │     │
│  │ (Parameter   │  │ (Class       │  │ (Test Forms  │     │
│  │  Collection) │  │  Confirmation)│  │  + Progress) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓ API calls
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Pydantic)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Rules Engine (Pure Functions)                  │  │
│  │  ┌──────────────────┐  ┌──────────────────────────┐ │  │
│  │  │ determine_class()│  │ assemble_test_plan()     │ │  │
│  │  │ (Table 3 lookup) │  │ (Applicability matrix)   │ │  │
│  │  └──────────────────┘  └──────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Rulepack Loader (YAML → Pydantic)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Versioned Rulepacks (YAML/JSON files)               │
│  • classification.yaml (Table 3 + Table 4)                  │
│  • test_applicability.yaml (Annex A/B matrix)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL)                           │
│  • instrument_profiles  • class_determinations              │
│  • test_plans           • environment_sessions              │
│  • environment_readings • audit_trail                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Architectural Decisions

**AD-1: Rules as Data, Not Code**
- All OIML R 76 classification and applicability rules stored in versioned YAML files
- Rules engine loads and interprets data; never hardcodes thresholds
- Enables auditable rule updates without code deployment

**AD-2: Pure Function Core**
- Classification and test plan assembly are pure functions
- No database queries, API calls, or LLM invocations in decision logic
- Fully unit-testable with deterministic outputs

**AD-3: Rulepack Versioning**
- Each test job pins a specific rulepack version on creation
- Jobs remain consistent even if rules are updated later
- Version stored in `class_determinations` and `test_plans` tables

**AD-4: Human-in-the-Loop for Ambiguity**
- System detects but never auto-resolves ambiguous classifications
- Explicit confirmation required, logged to audit trail
- No silent fallbacks or "best guess" behavior

## 2. Data Models

### 2.1 Pydantic Models (Backend)

```python
from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# ============ Rulepack Models ============

class ClassBand(BaseModel):
    class_: Literal["I", "II", "III", "IIII"]
    e_min_g: Decimal
    e_max_g: Optional[Decimal]
    n_min: int
    n_max: Optional[int]
    min_capacity_factor: int
    
    def matches(self, e: Decimal, n: Decimal) -> bool:
        """Check if (e, n) falls within this band's boundaries."""
        e_ok = (self.e_min_g <= e) and (not self.e_max_g or e <= self.e_max_g)
        n_ok = (self.n_min <= n) and (not self.n_max or n <= self.n_max)
        return e_ok and n_ok

class ClassificationRulepack(BaseModel):
    version: str  # e.g., "R76-1:2006"
    class_bands: List[ClassBand]
    multi_interval_ratios: dict[str, int]  # {"I": 50000, "II": 5000, ...}

class TestDefinition(BaseModel):
    id: str
    name: str
    clause_ref: str
    applies_if: str  # Python-evaluable expression
    variant_by: Optional[str] = None  # Field name for variant selection
    sequence: int  # Display order
    note: Optional[str] = None

class TestApplicabilityRulepack(BaseModel):
    version: str
    tests: List[TestDefinition]

# ============ Instrument Models ============

class SubRange(BaseModel):
    e: Decimal
    max_cap: Decimal
    min_cap: Optional[Decimal]

class InstrumentProfile(BaseModel):
    id: int
    model_id: int
    
    # Classification parameters
    e: Decimal
    max_capacity: Decimal
    min_capacity: Optional[Decimal]
    is_multi_range: bool
    is_multi_interval: bool
    sub_ranges: Optional[List[SubRange]]
    
    # Category parameters
    self_indicating_type: Literal["self_indicating", "semi_self_indicating", "non_self_indicating"]
    indication_type: Optional[Literal["digital", "analogue"]]  # Only if self_indicating
    is_electronic: bool
    has_tare_device: bool
    intended_use: Literal["general_trade", "direct_sales", "price_computing", "labelling", "grading"]
    
    def get(self, field_name: str):
        """Helper for variant resolution."""
        return getattr(self, field_name, None)

# ============ Classification Results ============

class ClassResult(BaseModel):
    status: Literal["DETERMINED", "AMBIGUOUS", "INVALID"]
    class_: Optional[str] = None  # Single determined class
    candidates: Optional[List[ClassBand]] = None  # For AMBIGUOUS
    reason: Optional[str] = None  # For INVALID
    computed_n: Decimal

class ClassDetermination(BaseModel):
    """Persisted classification with human confirmation."""
    id: int
    instrument_profile_id: int
    rulepack_version: str
    computed_n: Decimal
    status: str
    determined_class: Optional[str]
    candidates: Optional[dict]  # JSON serialized
    confirmed_by: Optional[int]  # User ID
    override_reason: Optional[str]
    confirmed_at: Optional[str]  # ISO timestamp

# ============ Test Plan Models ============

class ResolvedTest(BaseModel):
    id: str
    name: str
    clause_ref: str
    resolved_variant: Optional[str] = None
    sequence: int

class TestPlan(BaseModel):
    tests: List[ResolvedTest]
    class_: str
    total_count: int
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_count = len(self.tests)

# ============ Environment Models ============

class EnvironmentSession(BaseModel):
    id: int
    test_job_id: int
    start_temp: Decimal
    start_rel_h: Decimal
    start_time: str  # ISO timestamp
    start_bar_pres: Decimal

class EnvironmentReading(BaseModel):
    id: int
    test_run_id: int
    checkpoint: Literal["start", "max", "end"]
    temp: Decimal
    rel_h: Decimal
    time: str
    bar_pres: Decimal
    source: Literal["auto_carried", "manual_override"]
```

### 2.2 Database Schema

```sql
-- ============ Instrument Profiles (Extended) ============

ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS e DECIMAL(10,6);
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS max_capacity DECIMAL(12,3);
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS min_capacity DECIMAL(12,3);
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS is_multi_range BOOLEAN DEFAULT FALSE;
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS is_multi_interval BOOLEAN DEFAULT FALSE;
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS sub_ranges JSONB;
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS self_indicating_type VARCHAR(30);
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS indication_type VARCHAR(20);
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS is_electronic BOOLEAN;
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS has_tare_device BOOLEAN;
ALTER TABLE instrument_profiles ADD COLUMN IF NOT EXISTS intended_use VARCHAR(30);

-- ============ Class Determinations ============

CREATE TABLE class_determinations (
    id SERIAL PRIMARY KEY,
    instrument_profile_id INTEGER NOT NULL REFERENCES instrument_profiles(id),
    rulepack_version VARCHAR(50) NOT NULL,
    computed_n DECIMAL(12,6) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('DETERMINED', 'AMBIGUOUS', 'INVALID')),
    determined_class VARCHAR(10),
    candidates JSONB,
    confirmed_by INTEGER REFERENCES users(id),
    override_reason TEXT,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(instrument_profile_id, rulepack_version)
);

CREATE INDEX idx_class_det_profile ON class_determinations(instrument_profile_id);
CREATE INDEX idx_class_det_status ON class_determinations(status);

-- ============ Test Plans ============

CREATE TABLE test_plans (
    id SERIAL PRIMARY KEY,
    test_job_id INTEGER NOT NULL REFERENCES test_jobs(id),
    rulepack_version VARCHAR(50) NOT NULL,
    tests JSONB NOT NULL,  -- Array of ResolvedTest objects
    class VARCHAR(10) NOT NULL,
    total_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_job_id)
);

CREATE INDEX idx_test_plan_job ON test_plans(test_job_id);

-- ============ Environment Sessions ============

CREATE TABLE environment_sessions (
    id SERIAL PRIMARY KEY,
    test_job_id INTEGER NOT NULL REFERENCES test_jobs(id),
    start_temp DECIMAL(5,2) NOT NULL,
    start_rel_h DECIMAL(5,2) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    start_bar_pres DECIMAL(7,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_job_id)
);

-- ============ Environment Readings ============

CREATE TABLE environment_readings (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER NOT NULL REFERENCES test_runs(id),
    checkpoint VARCHAR(10) NOT NULL CHECK (checkpoint IN ('start', 'max', 'end')),
    temp DECIMAL(5,2) NOT NULL,
    rel_h DECIMAL(5,2) NOT NULL,
    time TIMESTAMP NOT NULL,
    bar_pres DECIMAL(7,2) NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('auto_carried', 'manual_override')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_run_id, checkpoint)
);

CREATE INDEX idx_env_reading_test ON environment_readings(test_run_id);
```

### 2.3 Zod Schemas (Frontend)

```typescript
// Mirror Pydantic models for client-side validation
import { z } from 'zod';

export const InstrumentProfileSchema = z.object({
  id: z.number().optional(),
  model_id: z.number(),
  
  // Classification parameters
  e: z.string().regex(/^\d+(\.\d+)?$/), // Decimal as string
  max_capacity: z.string().regex(/^\d+(\.\d+)?$/),
  min_capacity: z.string().regex(/^\d+(\.\d+)?$/).optional(),
  is_multi_range: z.boolean(),
  is_multi_interval: z.boolean(),
  sub_ranges: z.array(z.object({
    e: z.string(),
    max_cap: z.string(),
    min_cap: z.string().optional(),
  })).optional(),
  
  // Category parameters
  self_indicating_type: z.enum(['self_indicating', 'semi_self_indicating', 'non_self_indicating']),
  indication_type: z.enum(['digital', 'analogue']).optional(),
  is_electronic: z.boolean(),
  has_tare_device: z.boolean(),
  intended_use: z.enum(['general_trade', 'direct_sales', 'price_computing', 'labelling', 'grading']),
});

export const ClassResultSchema = z.object({
  status: z.enum(['DETERMINED', 'AMBIGUOUS', 'INVALID']),
  class_: z.string().optional(),
  candidates: z.array(z.any()).optional(),
  reason: z.string().optional(),
  computed_n: z.string(),
});

export const TestPlanSchema = z.object({
  tests: z.array(z.object({
    id: z.string(),
    name: z.string(),
    clause_ref: z.string(),
    resolved_variant: z.string().optional(),
    sequence: z.number(),
  })),
  class_: z.string(),
  total_count: z.number(),
});
```

## 3. Core Algorithms

### 3.1 Classification Engine

```python
from decimal import Decimal
from typing import List

def determine_class(
    e: Decimal,
    max_cap: Decimal,
    rulepack: ClassificationRulepack
) -> ClassResult:
    """
    Pure function: determine accuracy class from e and Max.
    
    Algorithm:
    1. Calculate n = Max / e
    2. Find all class bands where (e, n) falls within boundaries
    3. Return DETERMINED (1 match), AMBIGUOUS (2+ matches), or INVALID (0 matches)
    
    No I/O, no side effects, fully testable.
    """
    n = max_cap / e
    
    matches: List[ClassBand] = [
        band for band in rulepack.class_bands 
        if band.matches(e, n)
    ]
    
    if len(matches) == 0:
        return ClassResult(
            status="INVALID",
            computed_n=n,
            reason=f"No class band matches e={e}g, n={n:.2f}"
        )
    
    if len(matches) > 1:
        return ClassResult(
            status="AMBIGUOUS",
            computed_n=n,
            candidates=matches
        )
    
    return ClassResult(
        status="DETERMINED",
        computed_n=n,
        class_=matches[0].class_
    )


def suggest_min_capacity(e: Decimal, class_: str, rulepack: ClassificationRulepack) -> Decimal:
    """
    Suggest Min based on class-specific factor from Table 3.
    Technician can override.
    """
    band = next((b for b in rulepack.class_bands if b.class_ == class_), None)
    if not band:
        raise ValueError(f"Unknown class: {class_}")
    return band.min_capacity_factor * e
```

### 3.2 Test Plan Assembly

```python
def assemble_test_plan(
    instrument: InstrumentProfile,
    class_result: ClassResult,
    rulepack: TestApplicabilityRulepack
) -> TestPlan:
    """
    Pure function: build test list from instrument profile and determined class.
    
    Algorithm:
    1. Filter tests where applies_if evaluates to True
    2. Resolve variants (e.g., discrimination → digital/analogue sub-form)
    3. Sort by sequence number
    4. Return complete test plan
    """
    if class_result.status != "DETERMINED":
        raise ValueError("Cannot assemble test plan for non-determined class")
    
    # Build evaluation context
    ctx = {
        "class": class_result.class_,
        "electronic": instrument.is_electronic,
        "self_indicating": instrument.self_indicating_type != "non_self_indicating",
        "has_tare_device": instrument.has_tare_device,
        "intended_use": instrument.intended_use,
        "indication_type": instrument.indication_type,
    }
    
    applicable_tests: List[ResolvedTest] = []
    
    for test_def in rulepack.tests:
        # Evaluate applicability condition
        if not _evaluate_condition(test_def.applies_if, ctx):
            continue
        
        # Resolve variant if needed
        resolved_variant = None
        if test_def.variant_by:
            resolved_variant = instrument.get(test_def.variant_by)
        
        applicable_tests.append(ResolvedTest(
            id=test_def.id,
            name=test_def.name,
            clause_ref=test_def.clause_ref,
            resolved_variant=resolved_variant,
            sequence=test_def.sequence,
        ))
    
    # Sort by sequence
    applicable_tests.sort(key=lambda t: t.sequence)
    
    return TestPlan(
        tests=applicable_tests,
        class_=class_result.class_
    )


def _evaluate_condition(condition: str, context: dict) -> bool:
    """
    Safely evaluate applicability condition against context.
    
    Examples:
      "always" → True
      "electronic == true" → context["electronic"]
      "class in [II, III, IIII]" → context["class"] in ["II", "III", "IIII"]
    """
    if condition == "always":
        return True
    
    # Safe eval with restricted context (no builtins)
    try:
        return eval(condition, {"__builtins__": {}}, context)
    except Exception as e:
        # Log error and fail safe (don't include test if condition broken)
        print(f"Error evaluating condition '{condition}': {e}")
        return False
```

### 3.3 Environment Auto-Propagation

```python
def create_environment_readings_for_test(
    test_run_id: int,
    session: EnvironmentSession,
    test_duration_category: Literal["short", "time_spanning"]
) -> List[EnvironmentReading]:
    """
    Auto-create environment readings for a test based on session defaults.
    
    Short tests: copy session start to all three checkpoints
    Time-spanning tests: copy session start to "start" only; prompt for max/end
    """
    readings = [
        EnvironmentReading(
            test_run_id=test_run_id,
            checkpoint="start",
            temp=session.start_temp,
            rel_h=session.start_rel_h,
            time=session.start_time,
            bar_pres=session.start_bar_pres,
            source="auto_carried"
        )
    ]
    
    if test_duration_category == "short":
        # Auto-carry to max and end
        readings.extend([
            EnvironmentReading(
                test_run_id=test_run_id,
                checkpoint="max",
                temp=session.start_temp,
                rel_h=session.start_rel_h,
                time=session.start_time,
                bar_pres=session.start_bar_pres,
                source="auto_carried"
            ),
            EnvironmentReading(
                test_run_id=test_run_id,
                checkpoint="end",
                temp=session.start_temp,
                rel_h=session.start_rel_h,
                time=session.start_time,
                bar_pres=session.start_bar_pres,
                source="auto_carried"
            )
        ])
    
    return readings
```

## 4. UI Flow Design

### 4.1 Stage 1 — Parameter Collection

**Screen: Classification Parameters**
```
┌─────────────────────────────────────────────────────┐
│ Stage 1: Instrument Parameters                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│ [📷 Scan Nameplate Photo] ← Optional pre-fill      │
│                                                     │
│ Verification Scale Interval (e):                    │
│ ┌──────────┐ g                                     │
│ │  0.001   │                                        │
│ └──────────┘                                        │
│                                                     │
│ Maximum Capacity (Max):                             │
│ ┌──────────┐ kg                                    │
│ │  150     │                                        │
│ └──────────┘                                        │
│                                                     │
│ Minimum Capacity (Min):                             │
│ ┌──────────┐ kg  💡 Suggested: 0.020 kg           │
│ │  0.020   │     (20 × e for Class II)             │
│ └──────────┘                                        │
│                                                     │
│ ☐ Multi-range or multi-interval instrument         │
│                                                     │
│ ─────────────────────────────────────────────────  │
│                                                     │
│ Category Parameters:                                │
│                                                     │
│ Self-indicating type:                               │
│ ● Self-indicating  ○ Semi-self-indicating           │
│ ○ Non-self-indicating                              │
│                                                     │
│ Indication type:                                    │
│ ● Digital  ○ Analogue                              │
│                                                     │
│ Operating principle:                                │
│ ● Electronic  ○ Mechanical                         │
│                                                     │
│ ☑ Has tare device                                  │
│                                                     │
│ Intended use:                                       │
│ [General trade ▼]                                  │
│                                                     │
│                         [Continue to Classification]│
└─────────────────────────────────────────────────────┘
```

### 4.2 Stage 1.5 — Classification Confirmation

**Screen: Determined Class (Happy Path)**
```
┌─────────────────────────────────────────────────────┐
│ Classification Result                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ✓ Accuracy Class: II                               │
│                                                     │
│ Based on:                                           │
│   • e = 0.001 g                                     │
│   • Max = 150 kg                                    │
│   • n = 150,000                                     │
│                                                     │
│ This matches OIML R 76-1:2006 Table 3, row 2:      │
│   Class II: 0.001g ≤ e ≤ 0.05g, 100 ≤ n ≤ 100,000 │
│                                                     │
│                                                     │
│ Applicable Tests: 18 of 26 total tests             │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ ☐ 1. Weighing performance                    │   │
│ │ ☐ 2. Temperature effect on no-load           │   │
│ │ ☐ 3.1. Eccentricity using weights            │   │
│ │ ☐ 4.1. Discrimination (digital)              │   │
│ │ ☐ 5. Repeatability                           │   │
│ │ ... (13 more tests)                          │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [← Back]                 [Confirm & Start Testing] │
└─────────────────────────────────────────────────────┘
```

**Screen: Ambiguous Class**
```
┌─────────────────────────────────────────────────────┐
│ Classification Result — Confirmation Needed         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ⚠ Multiple Classes Match                           │
│                                                     │
│ Based on e = 0.05g, Max = 5kg, n = 100,000:        │
│                                                     │
│ Both Class II bands are valid:                      │
│ ● Class II (0.001–0.05g): Matches at upper e bound │
│ ● Class II (0.1g+): Matches at lower n bound       │
│                                                     │
│ This is a boundary case. Please confirm which       │
│ class applies based on nameplate or manufacturer    │
│ documentation.                                       │
│                                                     │
│ Selected Class: [Class II (0.001–0.05g) ▼]        │
│                                                     │
│ Reason for selection (required):                    │
│ ┌─────────────────────────────────────────────┐   │
│ │ Nameplate lists "Accuracy class: II (fine)"  │   │
│ │                                              │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [← Back]                            [Confirm Class] │
└─────────────────────────────────────────────────────┘
```

### 4.3 Stage 2 — Test Execution Dashboard

**Screen: Test Dashboard**
```
┌────────────────────────────────────────────────────────────┐
│ Test Execution — Class II Electronic Instrument            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Progress: 6 / 18 complete                                  │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░ 33%                 │
│                                                            │
│ [Environment: 23.2°C, 52% RH, 1013.2 hPa] [Edit Session]  │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Test Name              Status      Last Updated      │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ ✓ 1. Weighing perf.    PASSED      10:42 AM         │ │
│ │ ✓ 2. Temp effect       PASSED      11:15 AM         │ │
│ │ ✓ 3.1. Eccentricity    PASSED      11:30 AM         │ │
│ │ ✓ 4.1. Discrimination  PASSED      11:45 AM         │ │
│ │ ✓ 5. Repeatability     PASSED      12:00 PM         │ │
│ │ ⚠ 6.1. Zero return     IN PROGRESS 12:15 PM    [→]  │ │
│ │ ☐ 6.2. Creep           NOT STARTED             [→]  │ │
│ │ ☐ 7. Stability         NOT STARTED             [→]  │ │
│ │ ☐ 8. Tilting           NOT STARTED             [→]  │ │
│ │ ... (9 more tests)                                  │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│ Jump to: [Any test dropdown ▼]                            │
│                                                            │
│ [💾 Save & Exit]                    [📄 Generate Report]  │
└────────────────────────────────────────────────────────────┘
```

**Screen: Individual Test Form (Batched Entry)**
```
┌────────────────────────────────────────────────────────────┐
│ Test 5: Repeatability (A.4.10)                             │
│ ◀ Back to Dashboard                         Test 5 of 18   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Environment: [Start] 23.2°C, 52% RH, 1013.2 hPa  [Same]   │
│                                                            │
│ Load Test Load (approximately Max):                         │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │  #  Load (kg)  Indication (kg)  Error (e)   Status   │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │  1   150.000   150.001          +1.0        ✓ PASS   │ │
│ │  2   150.000   150.000           0.0        ✓ PASS   │ │
│ │  3   150.000   150.001          +1.0        ✓ PASS   │ │
│ │  4   150.000  [________] [Scan] [____]      ⋯        │ │
│ │  5   —                                      ⋯        │ │
│ │  6   —                                      ⋯        │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│ [+ Add Reading]                                            │
│                                                            │
│ MPE: ±1.0 e  (Class II at Max)                            │
│                                                            │
│ Overall Status: ✓ PASSED (3/3 within MPE)                 │
│                                                            │
│ [Save & Continue]                      [Mark Complete →]   │
└────────────────────────────────────────────────────────────┘
```

### 4.4 Stage 3 — Environment Session Setup

**Screen: Session Environment (One-Time)**
```
┌─────────────────────────────────────────────────────┐
│ Stage 3: Test Environment                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Enter conditions at test session start.             │
│ These will auto-populate all tests.                 │
│                                                     │
│ Temperature:         ┌──────┐ °C                    │
│                      │ 23.2 │                       │
│                      └──────┘                       │
│                                                     │
│ Relative Humidity:   ┌──────┐ %                     │
│                      │  52  │                       │
│                      └──────┘                       │
│                                                     │
│ Time:                ┌──────┐                       │
│                      │09:30 │ (auto-filled)        │
│                      └──────┘                       │
│                                                     │
│ Barometric Pressure: ┌────────┐ hPa                 │
│                      │ 1013.2 │                     │
│                      └────────┘                     │
│                                                     │
│ ℹ You can override per-test for long-running tests │
│   like span stability, damp heat, or endurance.    │
│                                                     │
│                                  [Start Testing →]  │
└─────────────────────────────────────────────────────┘
```

## 5. API Endpoints

### 5.1 Classification Flow

```
POST /api/v1/classification/determine
Request:
  {
    "e": "0.001",
    "max_capacity": "150",
    "rulepack_version": "R76-1:2006"
  }
Response:
  {
    "status": "DETERMINED",
    "class_": "II",
    "computed_n": "150000.000000",
    "reason": null
  }

POST /api/v1/classification/confirm
Request:
  {
    "instrument_profile_id": 123,
    "class_result": {...},
    "confirmed_by": 45,
    "override_reason": "Nameplate specifies Class II (fine)"
  }
Response:
  {
    "class_determination_id": 789
  }
```

### 5.2 Test Plan Flow

```
POST /api/v1/test-plans/assemble
Request:
  {
    "instrument_profile_id": 123,
    "class_determination_id": 789,
    "rulepack_version": "R76-1:2006"
  }
Response:
  {
    "test_plan_id": 456,
    "tests": [
      {
        "id": "1",
        "name": "Weighing performance",
        "clause_ref": "A.4.4 / A.5.3.1",
        "resolved_variant": null,
        "sequence": 1
      },
      ...
    ],
    "class_": "II",
    "total_count": 18
  }
```

### 5.3 Environment Management

```
POST /api/v1/environment/session
Request:
  {
    "test_job_id": 101,
    "start_temp": "23.2",
    "start_rel_h": "52",
    "start_time": "2026-09-28T09:30:00Z",
    "start_bar_pres": "1013.2"
  }
Response:
  {
    "environment_session_id": 202
  }

POST /api/v1/environment/reading/override
Request:
  {
    "test_run_id": 567,
    "checkpoint": "end",
    "temp": "24.1",
    "rel_h": "55",
    "time": "2026-09-28T15:45:00Z",
    "bar_pres": "1012.8"
  }
Response:
  {
    "environment_reading_id": 890,
    "source": "manual_override"
  }
```

## 6. Testing Strategy

### 6.1 Unit Tests (Pure Functions)

```python
# tests/test_classification.py

from hypothesis import given, strategies as st
from decimal import Decimal

@given(
    e=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("10")),
    max_cap=st.decimals(min_value=Decimal("1"), max_value=Decimal("10000"))
)
def test_determine_class_always_returns_valid_status(e, max_cap, rulepack):
    """Property: classification always returns one of three valid statuses."""
    result = determine_class(e, max_cap, rulepack)
    assert result.status in ["DETERMINED", "AMBIGUOUS", "INVALID"]

def test_class_ii_lower_bound():
    """Boundary: e=0.001g, n=100 exactly matches Class II lower bound."""
    rulepack = load_rulepack("R76-1:2006")
    result = determine_class(Decimal("0.001"), Decimal("0.1"), rulepack)
    assert result.status == "DETERMINED"
    assert result.class_ == "II"

def test_ambiguous_at_band_edge():
    """Known case: some (e, n) pairs match multiple bands."""
    rulepack = load_rulepack("R76-1:2006")
    result = determine_class(Decimal("0.05"), Decimal("5"), rulepack)
    assert result.status == "AMBIGUOUS"
    assert len(result.candidates) >= 2
```

### 6.2 Integration Tests

```python
# tests/test_test_plan_assembly.py

def test_electronic_instrument_gets_voltage_test():
    """Electronic instruments should always include voltage variation test."""
    instrument = InstrumentProfile(
        is_electronic=True,
        self_indicating_type="self_indicating",
        indication_type="digital",
        # ... other fields
    )
    class_result = ClassResult(status="DETERMINED", class_="II", computed_n=Decimal("150000"))
    rulepack = load_test_applicability_rulepack("R76-1:2006")
    
    plan = assemble_test_plan(instrument, class_result, rulepack)
    
    test_ids = [t.id for t in plan.tests]
    assert "11" in test_ids  # Test 11: Variations of voltage
```

### 6.3 End-to-End Tests

```python
# tests/test_e2e_classification_flow.py

async def test_full_classification_workflow(client, db_session):
    """E2E: Stage 1 → 1.5 → confirmed classification → test plan."""
    # Stage 1: Submit instrument profile
    response = await client.post("/api/v1/instrument-profiles", json={
        "model_id": 1,
        "e": "0.001",
        "max_capacity": "150",
        "is_electronic": True,
        # ... other fields
    })
    profile_id = response.json()["id"]
    
    # Stage 1.5: Determine class
    response = await client.post("/api/v1/classification/determine", json={
        "e": "0.001",
        "max_capacity": "150",
        "rulepack_version": "R76-1:2006"
    })
    assert response.json()["status"] == "DETERMINED"
    
    # Confirm classification
    response = await client.post("/api/v1/classification/confirm", json={
        "instrument_profile_id": profile_id,
        "class_result": response.json(),
        "confirmed_by": 1
    })
    class_det_id = response.json()["class_determination_id"]
    
    # Assemble test plan
    response = await client.post("/api/v1/test-plans/assemble", json={
        "instrument_profile_id": profile_id,
        "class_determination_id": class_det_id,
        "rulepack_version": "R76-1:2006"
    })
    test_plan = response.json()
    
    assert test_plan["class_"] == "II"
    assert test_plan["total_count"] > 0
    assert all(t["sequence"] > 0 for t in test_plan["tests"])
```

## 7. Implementation Phases

**Phase 1: Rulepack Foundation**
- YAML rulepack files for classification and test applicability
- Pydantic models for rulepack loading
- Validation and versioning infrastructure

**Phase 2: Classification Engine**
- Pure function implementations
- Hypothesis property tests
- API endpoints for Stage 1 and 1.5

**Phase 3: Test Plan Assembly**
- Test applicability evaluation
- Variant resolution logic
- Integration with classification results

**Phase 4: Frontend Flows**
- Stage 1 parameter collection form
- Stage 1.5 confirmation UI
- Stage 2 test dashboard and individual forms

**Phase 5: Environment Management**
- Session capture
- Auto-propagation logic
- Per-test override UI

**Phase 6: Integration & Polish**
- E2E testing
- Performance optimization
- Documentation and training materials

## 8. Security & Compliance

**Audit Trail Requirements:**
- All classification overrides logged with user ID, timestamp, and reason
- Rulepack version pinned and immutable per job
- Environment reading sources tracked (auto vs manual)

**Data Integrity:**
- Foreign key constraints on all cross-table references
- UNIQUE constraints prevent duplicate determinations per instrument
- CHECK constraints enforce valid enum values

**Access Control:**
- Classification confirmation requires authenticated user
- Override reasons mandatory for non-DETERMINED cases
- Audit log append-only with hash chaining (existing feature)

## 9. Performance Considerations

**Rulepack Caching:**
- Load YAML files once at startup
- Cache in memory per version
- Reload only on explicit version change

**Database Indexes:**
- Index on instrument_profile_id for joins
- Index on test_job_id for test plan lookups
- Composite index on (test_run_id, checkpoint) for environment readings

**UI Optimization:**
- Lazy load individual test forms
- Paginate long test lists (>20 tests)
- Debounce live pass/fail calculations

## 10. Open Questions & Verification Needed

1. **Multi-interval ratio validation** (Table 4): Verify formula Max_i / e_(i+1) ≥ threshold applies per partial range.
2. **Class I n_max exception** (§3.4.4): Confirm whether "no max" is truly unlimited or has conditional bounds.
3. **Test applicability rows marked VERIFY**: Require metrologist sign-off before production:
   - Test 3.2 (eccentricity rolling load)
   - Test 8 (tilting — Class I variant)
   - Test 14 (span stability applicability)
4. **Long test checkpoint timing**: Confirm R 76-2's exact requirements for "At max" timing in span stability and damp heat.
5. **Variant vs skip logic**: Double-check tilting test (§8) — is Class I truly a variant form or a conditional skip?
