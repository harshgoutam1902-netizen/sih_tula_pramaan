/**
 * Mock test plan generator.
 */

import type { ResolvedTest } from '@/types/api';

interface InstrumentParams {
  class_: string;
  is_electronic: boolean;
  self_indicating_type: string;
  has_tare_device: boolean;
}

const BASE_TESTS: Array<{
  id: string;
  name: string;
  duration: 'short' | 'time_spanning';
  condition?: (p: InstrumentParams) => boolean;
  reason?: string;
}> = [
  { id: 'MPE-1', name: 'MPE at Initial Verification', duration: 'short', reason: 'Required for all instruments' },
  { id: 'REP-1', name: 'Repeatability Test', duration: 'short', reason: 'Required for all instruments' },
  { id: 'ECC-1', name: 'Eccentric Loading', duration: 'short', reason: 'Required for all instruments' },
  { id: 'DISC-1', name: 'Discrimination Test', duration: 'short', reason: 'Required for all instruments' },
  { id: 'ELEC-1', name: 'Damp Heat Cyclic', duration: 'time_spanning', condition: (p) => p.is_electronic, reason: 'Electronic instrument' },
  { id: 'ELEC-2', name: 'Dry Heat', duration: 'time_spanning', condition: (p) => p.is_electronic, reason: 'Electronic instrument' },
  { id: 'ELEC-3', name: 'Cold Test', duration: 'time_spanning', condition: (p) => p.is_electronic, reason: 'Electronic instrument' },
  { id: 'ELEC-4', name: 'Mains Voltage Variation', duration: 'short', condition: (p) => p.is_electronic, reason: 'Electronic instrument' },
  { id: 'TARE-1', name: 'Tare Device Test', duration: 'short', condition: (p) => p.has_tare_device, reason: 'Has tare device' },
  { id: 'SENS-1', name: 'Sensitivity Test', duration: 'short', condition: (p) => p.self_indicating_type !== 'self_indicating', reason: 'Not self-indicating' },
];

export function mockGenerateTestPlan(params: InstrumentParams): ResolvedTest[] {
  const tests: ResolvedTest[] = [];
  let sequence = 1;
  
  for (const test of BASE_TESTS) {
    if (!test.condition || test.condition(params)) {
      tests.push({
        id: test.id,
        name: test.name,
        clause_ref: test.id,
        resolved_variant: test.reason || null,
        sequence: sequence++,
        duration_category: test.duration,
      });
    }
  }
  
  return tests;
}
