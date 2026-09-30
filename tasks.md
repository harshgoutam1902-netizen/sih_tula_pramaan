# Implementation Tasks: 3-Stage Smart Form System
### TulaPramaan — OIML R 76 Type Evaluation & Test Report Automation

## Task Organization

Tasks are grouped by implementation phase and ordered for dependency management. Each task includes:
- **ID**: Unique identifier
- **Phase**: Implementation phase (1-6)
- **Priority**: P0 (critical path) / P1 (important) / P2 (enhancement)
- **Dependencies**: Tasks that must complete first
- **Estimate**: T-shirt size (XS/S/M/L/XL)

---

## Phase 1: Rulepack Foundation

### T1.1: Create Rulepack Directory Structure
**Priority**: P0 | **Estimate**: XS | **Dependencies**: None

- [ ] Create `rulepacks/oiml-r76-1_2006/` directory
- [ ] Add `classification.yaml` file (empty template)
- [ ] Add `test_applicability.yaml` file (empty template)
- [ ] Add `README.md` documenting rulepack structure and versioning
- [ ] Create `.rulepacks-version` tracking file

**Acceptance Criteria:**
- Directory structure matches design spec
- Templates include schema comments
- README explains versioning strategy

---

### T1.2: Encode Classification Rules (Table 3)
**Priority**: P0 | **Estimate**: M | **Dependencies**: T1.1

- [ ] Encode all 6 class band rows from Table 3 into `classification.yaml`
- [ ] Add multi-interval ratios from Table 4
- [ ] Include source citations (OIML R 76-1:2006 § references)
- [ ] Add inline comments for boundary cases
- [ ] **CRITICAL**: Flag §3.4.4 Class I exception for review

**Acceptance Criteria:**
- All values match Table 3 exactly (use Decimal precision)
- YAML validates against schema
- Edge cases documented in comments

---

### T1.3: Encode Test Applicability Matrix
**Priority**: P0 | **Estimate**: L | **Dependencies**: T1.1

- [ ] Encode 17 test definitions from build spec into `test_applicability.yaml`
- [ ] Add `applies_if` conditions for each test
- [ ] Add `variant_by` fields for tests with sub-forms (discrimination, tilting)
- [ ] Add `sequence` numbers for display ordering
- [ ] Flag all rows marked "VERIFY" with TODO comments
- [ ] **BLOCKER**: Assign metrologist review task for VERIFY rows

**Acceptance Criteria:**
- All 17 tests encoded with correct clause references
- Conditions are Python-evaluable strings
- VERIFY rows clearly marked for review

---

### T1.4: Create Pydantic Rulepack Models
**Priority**: P0 | **Estimate**: M | **Dependencies**: T1.2, T1.3

- [ ] Create `models/rulepacks.py`
- [ ] Implement `ClassBand` model with `matches()` method
- [ ] Implement `ClassificationRulepack` model
- [ ] Implement `TestDefinition` model
- [ ] Implement `TestApplicabilityRulepack` model
- [ ] Add YAML loader with validation
- [ ] Write unit tests for YAML parsing

**Acceptance Criteria:**
- Models match design spec exactly
- YAML loader raises validation errors for invalid files
- Unit tests cover all model fields and validation rules

---

### T1.5: Rulepack Version Management System
**Priority**: P1 | **Estimate**: S | **Dependencies**: T1.4

- [ ] Create `services/rulepack_loader.py`
- [ ] Implement version-keyed cache (in-memory dict)
- [ ] Add loader function `load_rulepack(version: str)`
- [ ] Add reload trigger endpoint (admin only)
- [ ] Write tests for cache hit/miss behavior

**Acceptance Criteria:**
- Rulepacks loaded once per version at startup
- Cache invalidation works correctly
- Concurrent requests don't cause duplicate loads

---

## Phase 2: Classification Engine

### T2.1: Implement `determine_class()` Pure Function
**Priority**: P0 | **Estimate**: M | **Dependencies**: T1.4

- [ ] Create `services/classification_engine.py`
- [ ] Implement `determine_class(e, max_cap, rulepack)` function
- [ ] Calculate n = Max / e using Decimal arithmetic
- [ ] Match against class bands
- [ ] Return ClassResult with DETERMINED/AMBIGUOUS/INVALID status
- [ ] **RULE CHECK**: No I/O, no LLM calls, pure function only

**Acceptance Criteria:**
- Function signature matches design spec
- Returns correct ClassResult for all status types
- No side effects (passes pure function test)

---

### T2.2: Hypothesis Property Tests for Classification
**Priority**: P0 | **Estimate**: L | **Dependencies**: T2.1

- [ ] Create `tests/test_classification_properties.py`
- [ ] Write property test: status always one of three valid values
- [ ] Write property test: n calculation always equals max/e
- [ ] Write property test: DETERMINED status → exactly one candidate
- [ ] Write property test: AMBIGUOUS status → 2+ candidates
- [ ] Write property test: INVALID status → zero candidates
- [ ] Run 1000+ generated examples

**Acceptance Criteria:**
- All property tests pass with 1000+ examples
- Tests use hypothesis strategies for Decimal generation
- Coverage includes all class bands

---

### T2.3: Boundary & Edge Case Unit Tests
**Priority**: P0 | **Estimate**: M | **Dependencies**: T2.1

- [ ] Test Class II lower bound (e=0.001g, n=100)
- [ ] Test Class II upper bound (e=0.05g, n=100,000)
- [ ] Test known ambiguous case (boundary between bands)
- [ ] Test invalid case (e=0, should fail validation)
- [ ] Test invalid case (n < all band minimums)
- [ ] Test Class I exception case (if §3.4.4 resolved)

**Acceptance Criteria:**
- All boundary cases explicitly tested
- Known ambiguous cases return AMBIGUOUS status
- Invalid inputs handled gracefully with clear reason

---

### T2.4: Min Capacity Suggestion Function
**Priority**: P1 | **Estimate**: S | **Dependencies**: T2.1

- [ ] Implement `suggest_min_capacity(e, class_, rulepack)`
- [ ] Calculate Min = factor × e from class band
- [ ] Handle multi-range instruments (suggest per sub-range)
- [ ] Write unit tests for all five classes

**Acceptance Criteria:**
- Returns correct Min for each class
- Handles edge case where class unknown
- Tests cover all five accuracy classes

---

### T2.5: Database Schema — instrument_profiles Extensions
**Priority**: P0 | **Estimate**: M | **Dependencies**: None

- [ ] Write Alembic migration for `instrument_profiles` table
- [ ] Add columns: e, max_capacity, min_capacity
- [ ] Add columns: is_multi_range, is_multi_interval, sub_ranges (JSONB)
- [ ] Add columns: self_indicating_type, indication_type
- [ ] Add columns: is_electronic, has_tare_device, intended_use
- [ ] Add CHECK constraints for enum fields
- [ ] Run migration on dev database

**Acceptance Criteria:**
- Migration applies cleanly with no errors
- Rollback migration works correctly
- All constraints enforced at database level

---

### T2.6: Database Schema — class_determinations Table
**Priority**: P0 | **Estimate**: M | **Dependencies**: T2.5

- [ ] Write Alembic migration for new `class_determinations` table
- [ ] Add columns per design spec
- [ ] Add foreign key to `instrument_profiles`
- [ ] Add CHECK constraint on status field
- [ ] Add UNIQUE constraint on (instrument_profile_id, rulepack_version)
- [ ] Create indexes per design spec
- [ ] Run migration on dev database

**Acceptance Criteria:**
- Table created with all constraints
- Foreign keys enforce referential integrity
- Indexes exist for common query patterns

---

### T2.7: Pydantic Models for Classification Flow
**Priority**: P0 | **Estimate**: S | **Dependencies**: T2.5, T2.6

- [ ] Create `models/instrument.py`
- [ ] Implement `InstrumentProfile` model
- [ ] Implement `ClassResult` model
- [ ] Implement `ClassDetermination` model (DB row)
- [ ] Add validators for Decimal fields (precision, range)
- [ ] Write unit tests for model validation

**Acceptance Criteria:**
- Models match database schema exactly
- Zod equivalents defined for frontend
- Validation catches invalid inputs

---

### T2.8: API Endpoint — POST /classification/determine
**Priority**: P0 | **Estimate**: M | **Dependencies**: T2.1, T2.7

- [ ] Create `routers/classification.py`
- [ ] Implement `/classification/determine` endpoint
- [ ] Accept `e`, `max_capacity`, `rulepack_version` in request
- [ ] Call `determine_class()` function
- [ ] Return ClassResult JSON
- [ ] Add OpenAPI documentation
- [ ] Write integration tests

**Acceptance Criteria:**
- Endpoint returns 200 with valid ClassResult
- Handles invalid inputs with 400 errors
- OpenAPI docs auto-generated correctly

---

### T2.9: API Endpoint — POST /classification/confirm
**Priority**: P0 | **Estimate**: M | **Dependencies**: T2.6, T2.8

- [ ] Implement `/classification/confirm` endpoint
- [ ] Accept ClassResult + override reason + user ID
- [ ] Insert row into `class_determinations` table
- [ ] Log to audit trail (existing feature integration)
- [ ] Return class_determination_id
- [ ] Validate: AMBIGUOUS requires override_reason
- [ ] Write integration tests

**Acceptance Criteria:**
- DETERMINED confirmations work without override reason
- AMBIGUOUS confirmations require override reason (400 if missing)
- Audit trail entry created with correct fields

---

### T2.10: Frontend — Stage 1 Parameter Collection Form
**Priority**: P0 | **Estimate**: L | **Dependencies**: T2.7

- [ ] Create `components/Stage1Form.tsx`
- [ ] Build form for all classification parameters (e, Max, Min)
- [ ] Build form for all category parameters (self-indicating type, etc.)
- [ ] Add multi-range/interval toggle with sub-range inputs
- [ ] Integrate with nameplate photo OCR (existing feature)
- [ ] Add client-side validation (Zod schema)
- [ ] Disable "Continue" button until form valid
- [ ] Write component tests (React Testing Library)

**Acceptance Criteria:**
- Form matches UI mockup from design doc
- Validation errors shown inline
- OCR pre-fill works and shows "Confirm" prompt
- Responsive layout for tablet use

---

### T2.11: Frontend — Stage 1.5 Classification Confirmation UI
**Priority**: P0 | **Estimate**: L | **Dependencies**: T2.8, T2.10

- [ ] Create `components/ClassificationResult.tsx`
- [ ] Display DETERMINED result with explanation (e, n, matched band)
- [ ] Display AMBIGUOUS result with candidate list + reason textarea
- [ ] Display INVALID result with error message + "Go Back" button
- [ ] Show test plan preview (count + first few tests)
- [ ] Add "Confirm & Start Testing" button
- [ ] Write component tests for all three statuses

**Acceptance Criteria:**
- All three status types render correctly
- AMBIGUOUS flow requires reason before confirming
- Explanation text cites specific Table 3 row
- Test preview shows accurate count

---

## Phase 3: Test Plan Assembly

### T3.1: Implement `assemble_test_plan()` Pure Function
**Priority**: P0 | **Estimate**: M | **Dependencies**: T1.4, T2.1

- [ ] Create `services/test_plan_engine.py`
- [ ] Implement `assemble_test_plan(instrument, class_result, rulepack)`
- [ ] Build evaluation context from instrument + class
- [ ] Filter tests by `applies_if` condition
- [ ] Resolve variants (discrimination → digital/analogue, tilting → class-specific)
- [ ] Sort by sequence number
- [ ] **RULE CHECK**: No I/O, no LLM calls, pure function only

**Acceptance Criteria:**
- Function signature matches design spec
- Returns TestPlan with correct test count
- Variants resolved correctly per indication_type
- No side effects (passes pure function test)

---

### T3.2: Safe Condition Evaluator
**Priority**: P0 | **Estimate**: S | **Dependencies**: T3.1

- [ ] Implement `_evaluate_condition(condition, context)` helper
- [ ] Handle "always" special case
- [ ] Handle simple expressions (e.g., "electronic == true")
- [ ] Handle list membership (e.g., "class in [II, III]")
- [ ] Restrict eval to no builtins (security)
- [ ] Log errors and fail safe (return False)
- [ ] Write security tests (attempt to inject malicious code)

**Acceptance Criteria:**
- All condition types from rulepack evaluate correctly
- Malicious code injection blocked
- Invalid conditions log error and return False

---

### T3.3: Unit Tests for Test Plan Assembly
**Priority**: P0 | **Estimate**: M | **Dependencies**: T3.1, T3.2

- [ ] Test: Class II electronic gets all electronic-specific tests
- [ ] Test: Class I mechanical skips all electronic tests
- [ ] Test: Discrimination test resolves to "digital" variant
- [ ] Test: Tilting test includes Class I variant
- [ ] Test: Non-self-indicating skips sensitivity test
- [ ] Test: Tare device = false skips tare weighing test
- [ ] Test: Sequence ordering is correct

**Acceptance Criteria:**
- All test scenarios pass
- Coverage includes all conditional tests from rulepack
- Variant resolution tested for all variant_by fields

---

### T3.4: Database Schema — test_plans Table
**Priority**: P0 | **Estimate**: S | **Dependencies**: T2.6

- [ ] Write Alembic migration for `test_plans` table
- [ ] Add columns per design spec
- [ ] Add foreign key to `test_jobs`
- [ ] Add UNIQUE constraint on test_job_id
- [ ] Create index on test_job_id
- [ ] Run migration on dev database

**Acceptance Criteria:**
- Table created with all constraints
- UNIQUE constraint prevents duplicate plans per job
- Index supports fast lookup by job ID

---

### T3.5: Pydantic Models for Test Plan
**Priority**: P0 | **Estimate**: S | **Dependencies**: T3.4

- [ ] Create `models/test_plan.py`
- [ ] Implement `ResolvedTest` model
- [ ] Implement `TestPlan` model with auto-calculated `total_count`
- [ ] Add Zod equivalents for frontend
- [ ] Write unit tests for model construction

**Acceptance Criteria:**
- Models match database schema
- `total_count` auto-calculated correctly
- Zod schemas generate from Pydantic models

---

### T3.6: API Endpoint — POST /test-plans/assemble
**Priority**: P0 | **Estimate**: M | **Dependencies**: T3.1, T3.5

- [ ] Create `routers/test_plans.py`
- [ ] Implement `/test-plans/assemble` endpoint
- [ ] Accept instrument_profile_id + class_determination_id + rulepack_version
- [ ] Load instrument profile from database
- [ ] Load class determination from database
- [ ] Call `assemble_test_plan()` function
- [ ] Insert test plan into database
- [ ] Return TestPlan JSON
- [ ] Write integration tests

**Acceptance Criteria:**
- Endpoint returns 200 with TestPlan
- Test plan persisted to database
- Integration test covers full flow from profiles → plan

---

## Phase 4: Frontend Flows

### T4.1: Frontend — Stage 2 Test Dashboard
**Priority**: P0 | **Estimate**: XL | **Dependencies**: T3.6

- [ ] Create `components/TestDashboard.tsx`
- [ ] Display progress bar (completed / total)
- [ ] Display environment summary with "Edit Session" button
- [ ] Render test list table (name, status, last updated)
- [ ] Add status icons (✓ passed, ⚠ in progress, ☐ not started)
- [ ] Add click handler to open individual test form
- [ ] Add "Jump to" dropdown for quick navigation
- [ ] Add "Save & Exit" and "Generate Report" buttons
- [ ] Persist scroll position on navigation back
- [ ] Write component tests

**Acceptance Criteria:**
- Dashboard matches UI mockup from design doc
- Progress bar updates in real-time
- Non-linear navigation works (can jump to any test)
- State persists across page reloads

---

### T4.2: Frontend — Individual Test Form Template
**Priority**: P0 | **Estimate**: L | **Dependencies**: T4.1

- [ ] Create `components/TestForm.tsx` base component
- [ ] Implement R 76-2 table layout (Load / Indication / ΔL / Error / Ec / mpe)
- [ ] Add "Add Reading" button for batched entry
- [ ] Integrate display photo OCR for indication column
- [ ] Add live MPE calculation per row
- [ ] Show pass/fail indicator per row
- [ ] Calculate overall test status (all pass = PASSED)
- [ ] Add environment checkpoint fields (start/max/end)
- [ ] Add "Save & Continue" and "Mark Complete" buttons
- [ ] Write component tests

**Acceptance Criteria:**
- Table layout matches R 76-2 format exactly
- "Add Reading" adds row without page reload
- Live pass/fail shows green/red immediately
- Decimal precision preserved (no float rounding)

---

### T4.3: Frontend — Test Form Variants (Discrimination)
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.2

- [ ] Create `components/tests/DiscriminationTest.tsx`
- [ ] Implement digital sub-form (R 76-2 A.4.8.1)
- [ ] Implement analogue sub-form (R 76-2 A.4.8.2)
- [ ] Implement non-self-indicating sub-form (R 76-2 A.4.8.3)
- [ ] Render only resolved variant based on indication_type
- [ ] Write component tests for all three variants

**Acceptance Criteria:**
- Only one variant shown per instrument
- Each variant matches R 76-2 procedure exactly
- No "variant not found" errors in console

---

### T4.4: Frontend — Test Form Variants (Tilting)
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.2

- [ ] Create `components/tests/TiltingTest.tsx`
- [ ] Implement Class I variant (tilt based on level indicator limit)
- [ ] Implement Class II/III/IIII variant (standard tilting procedure)
- [ ] Add note explaining Class I special handling
- [ ] Write component tests for both variants

**Acceptance Criteria:**
- Class I variant shows different procedure
- Note text explains why Class I is different
- Both variants match R 76-2 clauses

---

### T4.5: Frontend — Batched Repetitive Tests
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.2

- [ ] Optimize TestForm for repetitive rounds (span stability 8×, tare 2×)
- [ ] Remove page transitions between rounds
- [ ] Show round counter (Round 1 of 8)
- [ ] Add "Copy previous round" helper button
- [ ] Auto-advance to next round on "Continue"
- [ ] Write UX tests for multi-round flow

**Acceptance Criteria:**
- No page reload between rounds
- Progress indicator shows current round
- Copy button works correctly

---

### T4.6: Frontend — Live Pass/Fail Feedback
**Priority**: P0 | **Estimate**: M | **Dependencies**: T4.2

- [ ] Implement client-side MPE evaluation
- [ ] Calculate error and corrected error per row
- [ ] Compare against MPE from rulepack
- [ ] Show ✓ green or ✗ red icon immediately on input
- [ ] Update overall test status badge in real-time
- [ ] Add debounce to avoid excessive re-renders
- [ ] Write performance tests (renders <100ms per keystroke)

**Acceptance Criteria:**
- Pass/fail appears within 100ms of typing
- No flickering or re-render lag
- Overall status updates correctly
- Color-blind accessible (icons + color)

---

## Phase 5: Environment Management

### T5.1: Database Schema — environment_sessions Table
**Priority**: P0 | **Estimate**: S | **Dependencies**: None

- [ ] Write Alembic migration for `environment_sessions` table
- [ ] Add columns per design spec
- [ ] Add foreign key to `test_jobs`
- [ ] Add UNIQUE constraint on test_job_id
- [ ] Run migration on dev database

**Acceptance Criteria:**
- Table created with all constraints
- One session per test job enforced

---

### T5.2: Database Schema — environment_readings Table
**Priority**: P0 | **Estimate**: S | **Dependencies**: T5.1

- [ ] Write Alembic migration for `environment_readings` table
- [ ] Add columns per design spec
- [ ] Add foreign key to `test_runs`
- [ ] Add CHECK constraint on checkpoint and source enums
- [ ] Add UNIQUE constraint on (test_run_id, checkpoint)
- [ ] Create index on test_run_id
- [ ] Run migration on dev database

**Acceptance Criteria:**
- Table created with all constraints
- UNIQUE constraint prevents duplicate checkpoints per test

---

### T5.3: Environment Auto-Propagation Service
**Priority**: P0 | **Estimate**: M | **Dependencies**: T5.2

- [ ] Create `services/environment_service.py`
- [ ] Implement `create_environment_readings_for_test()`
- [ ] Auto-create "start" reading from session
- [ ] For short tests: auto-create "max" and "end" from session
- [ ] For time-spanning tests: create "start" only, prompt for max/end
- [ ] Add `update_environment_reading()` for manual override
- [ ] Mark override with source = "manual_override"
- [ ] Write unit tests

**Acceptance Criteria:**
- Short tests get all three readings auto-carried
- Time-spanning tests get only "start" auto-carried
- Overrides tracked with correct source field

---

### T5.4: Time-Spanning Test Configuration
**Priority**: P1 | **Estimate**: S | **Dependencies**: T5.3

- [ ] Add `duration_category` field to TestDefinition rulepack
- [ ] Mark tests as "short" or "time_spanning" in test_applicability.yaml
- [ ] Update `assemble_test_plan()` to include duration_category
- [ ] Write tests for correct categorization

**Acceptance Criteria:**
- Span stability, damp heat, endurance, creep, warm-up marked "time_spanning"
- All other tests marked "short"
- Test plan includes duration_category per test

---

### T5.5: API Endpoint — POST /environment/session
**Priority**: P0 | **Estimate**: S | **Dependencies**: T5.1

- [ ] Create `routers/environment.py`
- [ ] Implement `/environment/session` endpoint
- [ ] Accept test_job_id + start temp/humidity/time/pressure
- [ ] Insert row into `environment_sessions` table
- [ ] Return environment_session_id
- [ ] Write integration tests

**Acceptance Criteria:**
- Endpoint creates session successfully
- UNIQUE constraint prevents duplicate sessions
- Returns session ID for subsequent calls

---

### T5.6: API Endpoint — POST /environment/reading/override
**Priority**: P0 | **Estimate**: S | **Dependencies**: T5.2, T5.3

- [ ] Implement `/environment/reading/override` endpoint
- [ ] Accept test_run_id + checkpoint + new readings
- [ ] Call `update_environment_reading()` service
- [ ] Return updated reading with source = "manual_override"
- [ ] Write integration tests

**Acceptance Criteria:**
- Override updates existing reading
- Source field set to "manual_override"
- Audit trail entry created (existing feature)

---

### T5.7: Frontend — Stage 3 Environment Session Form
**Priority**: P0 | **Estimate**: M | **Dependencies**: T5.5

- [ ] Create `components/EnvironmentSessionForm.tsx`
- [ ] Build form for temp, humidity, time, barometric pressure
- [ ] Auto-fill time with current timestamp
- [ ] Show info message about auto-propagation
- [ ] Add "Start Testing" button
- [ ] Write component tests

**Acceptance Criteria:**
- Form matches UI mockup
- Time auto-filled on load
- Info message explains what happens next
- Validation enforces required fields

---

### T5.8: Frontend — Environment Override in Test Forms
**Priority**: P1 | **Estimate**: M | **Dependencies**: T5.6, T4.2

- [ ] Add environment checkpoint fields to TestForm component
- [ ] For short tests: show read-only carried values with "Override" button
- [ ] For time-spanning tests: show editable "At max" and "At end" fields
- [ ] Add override indicator (icon or badge)
- [ ] Call override API on save
- [ ] Write component tests

**Acceptance Criteria:**
- Short tests show read-only unless overridden
- Time-spanning tests prompt for max/end
- Override indicator visible when source = manual

---

### T5.9: Frontend — Consolidated Environment Summary
**Priority**: P1 | **Estimate**: S | **Dependencies**: T5.2

- [ ] Create `components/EnvironmentSummary.tsx`
- [ ] Query all environment_readings for test job
- [ ] Calculate min/max/avg per field
- [ ] Display as read-only table in final report
- [ ] Add note: "Consolidated from per-test records"
- [ ] Write component tests

**Acceptance Criteria:**
- Summary shows correct aggregated values
- No editable fields (read-only)
- Note clearly states this is derived data

---

## Phase 6: Integration & Polish

### T6.1: End-to-End Test — Full Workflow
**Priority**: P0 | **Estimate**: L | **Dependencies**: All previous tasks

- [ ] Create `tests/test_e2e_full_workflow.py`
- [ ] Test: Create instrument profile → classify → confirm → assemble plan
- [ ] Test: Set environment session → complete one test → verify readings
- [ ] Test: Override environment → verify source field
- [ ] Test: Complete all tests → generate report (stub)
- [ ] Run against staging database
- [ ] Verify audit trail entries created

**Acceptance Criteria:**
- Full workflow passes without errors
- All database tables populated correctly
- Audit trail complete and chained

---

### T6.2: Performance Optimization — Rulepack Loading
**Priority**: P1 | **Estimate**: M | **Dependencies**: T1.5

- [ ] Profile rulepack load times
- [ ] Optimize YAML parsing (use LibYAML if slow)
- [ ] Add cache warming on startup
- [ ] Add metrics logging (load time per version)
- [ ] Load test with 100 concurrent classification requests

**Acceptance Criteria:**
- Rulepack loads in <100ms
- Cache hit rate >95% after warmup
- No cache contention under load

---

### T6.3: Performance Optimization — Frontend Test Dashboard
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.1

- [ ] Profile dashboard render time with 30+ tests
- [ ] Implement virtualized scrolling if >20 tests
- [ ] Lazy load test form components
- [ ] Add loading skeletons for async fetches
- [ ] Measure First Contentful Paint (target <1s)

**Acceptance Criteria:**
- Dashboard loads in <1s with 30 tests
- Scroll performance smooth (60fps)
- No layout shift during loading

---

### T6.4: Metrologist Review — Test Applicability Matrix
**Priority**: P0 (BLOCKER) | **Estimate**: XL | **Dependencies**: T1.3

- [ ] **HUMAN TASK**: Assign metrologist to review test_applicability.yaml
- [ ] Provide R 76-1 and R 76-2 PDFs for cross-reference
- [ ] Review all rows marked "VERIFY" in build spec
- [ ] Confirm Test 3.2 (eccentricity rolling load) applicability
- [ ] Confirm Test 8 (tilting) Class I behavior
- [ ] Confirm Test 14 (span stability) applicability
- [ ] Resolve §3.4.4 Class I n_max exception
- [ ] Sign off on final rulepack version
- [ ] Update YAML with review findings

**Acceptance Criteria:**
- All VERIFY flags resolved with clause citations
- Metrologist signature on review document
- No ambiguous applicability conditions remain

---

### T6.5: Security Audit — Condition Evaluator
**Priority**: P0 | **Estimate**: M | **Dependencies**: T3.2

- [ ] Review `_evaluate_condition()` for injection risks
- [ ] Test with malicious YAML (e.g., `__import__('os').system('rm -rf /')`)
- [ ] Verify eval restricted to safe context
- [ ] Add input sanitization if needed
- [ ] Penetration test with security team
- [ ] Document security model in README

**Acceptance Criteria:**
- No code execution vulnerabilities
- Security team sign-off
- Security test suite added to CI

---

### T6.6: Documentation — Developer Guide
**Priority**: P1 | **Estimate**: M | **Dependencies**: All previous tasks

- [ ] Write `docs/3-stage-form-developer-guide.md`
- [ ] Document rulepack structure and versioning
- [ ] Document classification engine architecture
- [ ] Document test plan assembly algorithm
- [ ] Add code examples for common tasks
- [ ] Add troubleshooting section
- [ ] Add architecture diagrams (generate from design.md)

**Acceptance Criteria:**
- New developer can understand system in <1 hour
- All public APIs documented
- Diagrams render correctly in Markdown

---

### T6.7: Documentation — User Guide (Technician Workflow)
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.1, T5.7

- [ ] Write `docs/3-stage-form-user-guide.md`
- [ ] Document Stage 1 parameter collection with screenshots
- [ ] Document Stage 1.5 classification confirmation
- [ ] Document Stage 2 test execution with examples
- [ ] Document Stage 3 environment setup
- [ ] Add FAQs (e.g., "What if classification is ambiguous?")
- [ ] Record video walkthrough (optional but recommended)

**Acceptance Criteria:**
- Technician can complete workflow without assistance
- Screenshots show actual UI (not mockups)
- FAQ covers common questions from pilot testing

---

### T6.8: Accessibility Audit — WCAG 2.1 AA Compliance
**Priority**: P1 | **Estimate**: M | **Dependencies**: T4.1, T4.2

- [ ] Run automated accessibility scan (axe-core)
- [ ] Test keyboard navigation (tab order, focus indicators)
- [ ] Test screen reader compatibility (NVDA / JAWS)
- [ ] Verify color contrast ratios (pass/fail indicators)
- [ ] Add ARIA labels where needed
- [ ] Test with browser zoom (200%)
- [ ] Generate accessibility report

**Acceptance Criteria:**
- Zero critical or serious axe violations
- Full keyboard navigation functional
- Screen reader announces all status changes
- Color contrast meets WCAG AA (4.5:1)

---

### T6.9: Pilot Testing with 3 Technicians
**Priority**: P0 | **Estimate**: XL | **Dependencies**: T6.7

- [ ] **HUMAN TASK**: Recruit 3 technicians for pilot
- [ ] Provide training on new 3-stage workflow
- [ ] Assign each pilot 2-3 real instruments to test
- [ ] Observe workflow (screen recording + think-aloud)
- [ ] Collect feedback via survey
- [ ] Identify pain points and usability issues
- [ ] Prioritize fixes based on severity

**Acceptance Criteria:**
- All pilots complete at least one full workflow
- <3 critical usability issues identified
- Feedback documented in issue tracker

---

### T6.10: Bug Fixes from Pilot Testing
**Priority**: P0 | **Estimate**: Variable | **Dependencies**: T6.9

- [ ] Triage pilot feedback issues
- [ ] Fix P0 blockers (workflow-breaking bugs)
- [ ] Fix P1 high-impact issues (major usability problems)
- [ ] Defer P2 enhancements to post-launch backlog
- [ ] Re-test fixed issues with pilot participants

**Acceptance Criteria:**
- All P0 and P1 issues resolved
- Pilots confirm fixes work
- Regression test suite updated

---

### T6.11: Deployment Preparation
**Priority**: P0 | **Estimate**: M | **Dependencies**: T6.10

- [ ] Create production rulepack directory
- [ ] Write deployment runbook (migration steps)
- [ ] Configure production database backup
- [ ] Set up monitoring alerts (classification errors, API latency)
- [ ] Create rollback plan
- [ ] Smoke test on staging environment

**Acceptance Criteria:**
- Runbook tested on staging
- Monitoring dashboards operational
- Rollback tested successfully

---

### T6.12: Production Deployment
**Priority**: P0 | **Estimate**: S | **Dependencies**: T6.11

- [ ] **HUMAN TASK**: Schedule deployment window
- [ ] Run database migrations
- [ ] Deploy backend services
- [ ] Deploy frontend build
- [ ] Verify rulepack loaded correctly
- [ ] Run smoke tests on production
- [ ] Monitor error logs for 24 hours

**Acceptance Criteria:**
- Zero critical errors in first 24 hours
- All smoke tests pass
- Rollback plan ready if needed

---

## Summary

**Total Tasks**: 72
**Critical Path (P0)**: 42 tasks
**Estimated Timeline**: 8-12 weeks (depends on team size and parallel workstreams)

**Key Dependencies**:
- T6.4 (Metrologist Review) is a blocker for production deployment
- T6.9 (Pilot Testing) cannot start until all Phase 4-5 tasks complete
- T1.3 (Test Applicability Matrix) gates all test plan work

**Risk Mitigation**:
- Start T6.4 (Metrologist Review) early, even before code is written
- Run T6.5 (Security Audit) as soon as T3.2 completes, don't wait for Phase 6
- Identify pilot technicians early (before T4.1 completes)

**Recommended Staffing**:
- 2 backend engineers (Phase 1-3)
- 2 frontend engineers (Phase 4-5)
- 1 QA engineer (testing tasks)
- 1 metrologist (domain review)
- 1 technical writer (documentation)
