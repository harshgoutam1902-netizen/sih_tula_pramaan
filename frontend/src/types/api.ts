/**
 * API type definitions matching backend Pydantic models.
 * 
 * These types should stay in sync with backend/models/*.py
 */

// ========== Classification Types ==========

export type ClassificationStatus = "DETERMINED" | "AMBIGUOUS" | "INVALID";

export interface ClassBandCandidate {
  class: string;
  e_range: string;
  n_range: string;
  note?: string;
}

export interface ClassResult {
  status: ClassificationStatus;
  computed_n: string; // Decimal as string
  class_?: string | null;
  candidates?: ClassBandCandidate[] | null;
  reason?: string | null;
  suggested_min_capacity?: string | null;
}

export interface DetermineClassRequest {
  e: string;
  max_capacity: string;
  rulepack_version?: string;
}

export interface ConfirmClassificationRequest {
  instrument_profile_id: number;
  e: string;
  max_capacity: string;
  rulepack_version: string;
  status: ClassificationStatus;
  determined_class: string | null;
  computed_n: string;
  override_reason?: string | null;
  confirmed_by: number;
}

export interface ConfirmClassificationResponse {
  class_determination_id: number;
  message: string;
}

// ========== Instrument Types ==========

export type SelfIndicatingType = "self_indicating" | "semi_self_indicating" | "non_self_indicating";
export type IndicationType = "digital" | "analogue";
export type IntendedUse = "general_trade" | "direct_sales" | "price_computing" | "labelling" | "grading";

export interface SubRange {
  e: string;
  max_cap: string;
  min_cap?: string;
}

export interface InstrumentProfile {
  id?: number;
  model_id: number;
  
  // Classification parameters
  e: string;
  max_capacity: string;
  min_capacity?: string;
  is_multi_range: boolean;
  is_multi_interval: boolean;
  sub_ranges?: SubRange[];
  
  // Category parameters
  self_indicating_type: SelfIndicatingType;
  indication_type?: IndicationType;
  is_electronic: boolean;
  has_tare_device: boolean;
  intended_use: IntendedUse;
}

// ========== Test Plan Types ==========

export type DurationCategory = "short" | "time_spanning";

export interface ResolvedTest {
  id: string;
  name: string;
  clause_ref: string;
  resolved_variant?: string | null;
  sequence: number;
  duration_category: DurationCategory;
}

export interface TestPlan {
  tests: ResolvedTest[];
  class: string;
  total_count: number;
}

export interface TestPlanSummary {
  total_count: number;
  class: string;
  short_tests: number;
  time_spanning_tests: number;
  performance_tests: number;
  environmental_tests: number;
  checklist_tests: number;
  first_test: string;
  last_test: string;
}

export interface AssembleTestPlanRequest {
  instrument_profile_id: number;
  class_determination_id: number;
  rulepack_version?: string;
}

export interface AssembleTestPlanResponse {
  test_plan_id: number;
  test_job_id: number;
  tests: ResolvedTest[];
  class: string;
  total_count: number;
  summary: TestPlanSummary;
}

// ========== Environment Types ==========

export interface EnvironmentSession {
  id?: number;
  test_job_id: number;
  start_temp: string;
  start_rel_h: string;
  start_time: string; // ISO timestamp
  start_bar_pres: string;
  created_at?: string;
}

export type Checkpoint = "start" | "max" | "end";
export type ReadingSource = "auto_carried" | "manual_override";

export interface EnvironmentReading {
  id?: number;
  test_run_id: number;
  checkpoint: Checkpoint;
  temp: string;
  rel_h: string;
  time: string;
  bar_pres: string;
  source: ReadingSource;
  created_at?: string;
  updated_at?: string | null;
}

export interface CreateEnvironmentSessionRequest {
  test_job_id: number;
  start_temp: string;
  start_rel_h: string;
  start_time: string;
  start_bar_pres: string;
}

export interface OverrideEnvironmentReadingRequest {
  test_run_id: number;
  checkpoint: Checkpoint;
  temp: string;
  rel_h: string;
  time: string;
  bar_pres: string;
}

export interface EnvironmentSummary {
  test_job_id: number;
  reading_count: number;
  temperature: {
    min: number;
    max: number;
    avg: number;
    unit: string;
  };
  relative_humidity: {
    min: number;
    max: number;
    avg: number;
    unit: string;
  };
  barometric_pressure: {
    min: number;
    max: number;
    avg: number;
    unit: string;
  };
  note: string;
}

// ========== API Response Types ==========

export interface ApiError {
  detail: string;
}

export interface ApiStatus {
  status: string;
  version: string;
  environment: string;
  features: {
    ocr_enabled: boolean;
    live_mpe_feedback: boolean;
    multi_range_support: boolean;
    batch_repetitive_tests: boolean;
    environment_auto_propagation: boolean;
  };
  rulepack: {
    default_version: string;
    cache_enabled: boolean;
  };
}
