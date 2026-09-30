# Requirements: 3-Stage Smart Form System
### TulaPramaan — OIML R 76 Type Evaluation & Test Report Automation

## 1. Core Principle

**The AI layer never decides class, test applicability, MPE, or pass/fail.** A deterministic rules engine handles all regulatory decisions. AI only assists with OCR, prose generation, explanations, and proposing rulepack updates for human approval.

## 2. Functional Requirements

### 2.1 Stage 1 — Classification & Category Parameters

**FR-1.1** The system shall collect the following classification parameters:
- Verification scale interval (e)
- Maximum capacity (Max)
- Minimum capacity (Min) — optional, with system-suggested default
- Multi-range/multi-interval flag
- For multi-range/interval: e₁..eᵣ and Max₁..Maxᵣ per sub-range

**FR-1.2** The system shall collect the following category parameters:
- Self-indicating type: self-indicating / semi-self-indicating / non-self-indicating
- If self-indicating: indication type (digital / analogue)
- Operating principle: electronic / mechanical
- Has tare device: yes / no
- Intended use: general trade / direct sales / price-computing / labelling / grading

**FR-1.3** The system shall support pre-filling Stage 1 fields from nameplate photo OCR, requiring human confirmation before progression.

### 2.2 Stage 1.5 — Deterministic Routing Engine

**FR-1.5.1** The system shall implement a pure function `determine_class()` that:
- Calculates n = Max / e
- Matches against OIML R 76-1:2006 Table 3 class bands
- Returns DETERMINED (single match), AMBIGUOUS (multiple matches), or INVALID (no match)
- Never auto-resolves ambiguous classifications

**FR-1.5.2** The system shall implement `assemble_test_plan()` that:
- Evaluates test applicability based on instrument profile and determined class
- Resolves test variants (e.g., discrimination test by indication type)
- Returns a complete, ordered test plan

**FR-1.5.3** Ambiguous or invalid classifications shall:
- Block auto-progression to Stage 2
- Display detection reasoning to the technician
- Require explicit confirmation with logged reason
- Record override in audit trail

### 2.3 Stage 2 — Dynamic Test Form Assembly

**FR-2.1** The system shall display the complete test plan immediately after Stage 1.5:
- Total count of applicable tests
- Progress indicator showing current position
- Full checklist visible up front

**FR-2.2** The system shall allow non-linear test execution:
- Tests can be completed in any order
- Partial progress can be saved
- Technician can resume from any point
- Current status visible for each test (not started / in progress / completed)

**FR-2.3** Each test form shall:
- Match R 76-2 field layout (Load L / Indication I / Additional load ΔL / Error E / Corrected error Ec / mpe)
- Pull MPE values from rulepack based on determined class
- Render only the resolved variant for variant tests
- Support "add another reading" for repetitive measurements without page transitions

**FR-2.4** The system shall provide live pass/fail feedback:
- Evaluate against MPE as values are entered
- Display visual indicators (green/red) per measurement
- Update overall test status in real-time

**FR-2.5** The system shall support auto-fill for readings:
- Display photo OCR for indication values
- Serial cable integration for digital instruments
- Manual entry as fallback

**FR-2.6** Repetitive test rounds shall be batched:
- Span stability's 8 measurements on one continuous screen
- Damp heat's 3 sub-tests grouped
- Tare's 2 passes presented together
- Minimal page transitions during data entry

### 2.4 Stage 3 — Environment Capture

**FR-3.1** The system shall capture session-start environment once:
- Temperature
- Relative humidity
- Time
- Barometric pressure

**FR-3.2** Session-start values shall auto-propagate to all tests' "At start" fields.

**FR-3.3** For time-spanning tests (span stability, damp heat, endurance, creep, warm-up):
- Prompt for "At max" and "At end" readings
- Allow manual override per test

**FR-3.4** For short tests:
- Auto-carry session-start values to "At max" and "At end"
- Allow override if technician flags a change

**FR-3.5** Generate consolidated environment summary for final report:
- Read-only rollup of per-test records
- Not a separate data entry point

## 3. Data Requirements

### 3.1 Rulepack Data (Versioned YAML/JSON)

**DR-1.1** Classification rulepack (`rulepacks/oiml-r76-1_2006/classification.yaml`):
- Class bands from Table 3 (e_min, e_max, n_min, n_max, min_capacity_factor)
- Multi-interval ratios from Table 4

**DR-1.2** Test applicability rulepack (`rulepacks/oiml-r76-1_2006/test_applicability.yaml`):
- Test ID, name, clause reference
- Applicability conditions (always / conditional)
- Variant rules (indication type, class-specific behavior)
- Test sequence ordering

**DR-1.3** All rulepack YAML rows marked "VERIFY" must be confirmed against full Annex text before production deployment.

### 3.2 Database Schema Extensions

**DR-2.1** `instrument_profiles` table additions:
- e, max_capacity, min_capacity
- is_multi_range, is_multi_interval, sub_ranges (JSONB)
- self_indicating_type, indication_type
- is_electronic, has_tare_device, intended_use

**DR-2.2** New `class_determinations` table:
- instrument_profile_id, rulepack_version
- computed_n, status (DETERMINED / AMBIGUOUS / INVALID)
- determined_class, candidates (JSONB)
- confirmed_by, override_reason, confirmed_at

**DR-2.3** New `test_plans` table:
- test_job_id, rulepack_version
- tests (JSONB — resolved list with variants)

**DR-2.4** New `environment_sessions` table:
- test_job_id
- start_temp, start_rel_h, start_time, start_bar_pres

**DR-2.5** New `environment_readings` table:
- test_run_id, checkpoint (start / max / end)
- temp, rel_h, time, bar_pres
- source (auto_carried / manual_override)

## 4. Non-Functional Requirements

### 4.1 Architecture

**NFR-1.1** Classification and test applicability logic shall be:
- Implemented as pure functions with no I/O side effects
- Fully unit-testable
- Free of LLM calls in decision paths

**NFR-1.2** All regulatory decisions shall be:
- Deterministic and reproducible
- Based on versioned rulepack data
- Auditable with clear reasoning trail

### 4.2 Testing

**NFR-2.1** Classification engine shall have:
- Hypothesis property-based tests covering all five class bands
- Boundary case tests (e/n at band edges)
- Ambiguous and invalid case coverage
- 100% coverage of decision branches

**NFR-2.2** Test applicability rules shall have:
- Unit tests per rule condition
- Integration tests for variant resolution
- Verification against R 76-2 Annex text

### 4.3 Usability (Stress Reduction Features)

**NFR-3.1** Transparency:
- Show complete test plan immediately after classification
- Display progress indicator throughout
- No mystery queue that reveals more work incrementally

**NFR-3.2** Flexibility:
- Non-linear workflow support
- Save and resume at any point
- No forced sequential progression

**NFR-3.3** Efficiency:
- Auto-fill via OCR and serial integration
- Batch repetitive measurements
- Minimal page transitions for related entries

**NFR-3.4** Feedback:
- Live pass/fail evaluation
- Visual indicators per measurement
- Real-time overall test status

**NFR-3.5** Long-running test support:
- Multi-session capability for endurance/span stability
- Persistent state across days
- Clear indication of time-spanning tests

### 4.4 Compliance & Audit

**NFR-4.1** All classification overrides shall be:
- Logged with timestamp and user
- Require written reason
- Preserved in hash-chained audit trail

**NFR-4.2** Rulepack version shall be:
- Pinned per test job
- Immutable once job starts
- Traceable in final report

**NFR-4.3** Environment readings shall:
- Preserve per-test source tracking
- Distinguish auto-carried vs manual override
- Support traceability requirements

## 5. Technology Stack Requirements

**TR-1** Backend: FastAPI + Pydantic v2
- Rulepack models as Pydantic classes
- YAML loading with validation
- Pure function classification engine

**TR-2** Frontend: React + TypeScript
- Zod schemas mirroring Pydantic models
- Client-side validation matching backend
- Progressive enhancement for OCR features

**TR-3** Database: PostgreSQL with Alembic migrations
- JSONB for flexible sub-structures
- Foreign key constraints on rulepack_version
- Migration scripts for schema extensions

**TR-4** Testing: pytest + hypothesis
- Property-based tests for classification
- Integration tests for test plan assembly
- Fixture-based test data management

**TR-5** Precision: Python Decimal for all calculations
- No floating-point arithmetic in MPE evaluation
- Deterministic rounding per OIML rules

## 6. Out of Scope

**OS-1** LLM-based classification decisions (architectural rule violation)
**OS-2** LLM-based test applicability decisions (architectural rule violation)
**OS-3** LLM-based pass/fail evaluation (architectural rule violation)
**OS-4** Automatic test ordering optimization (maintain R 76-2 standard sequence)
**OS-5** Multi-language support (English only for v1)

## 7. Acceptance Criteria Summary

- [ ] Class bands loaded from versioned rulepack (not hardcoded)
- [ ] `determine_class()` is pure function with hypothesis tests
- [ ] Ambiguous classifications require confirmation and audit logging
- [ ] Test applicability matrix verified against full Annex text
- [ ] Discrimination test variants implemented correctly
- [ ] Tilting test class-I behavior as variant (not skip)
- [ ] Environment auto-propagation with per-test override
- [ ] Final report environment section is read-only rollup
- [ ] No LLM calls in classification or test applicability paths
- [ ] Complete test plan visible immediately after Stage 1.5
- [ ] Non-linear test execution supported
- [ ] Live pass/fail feedback operational
- [ ] Repetitive tests batched without page transitions
- [ ] Save/resume functionality working across sessions
