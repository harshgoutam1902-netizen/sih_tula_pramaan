/**
 * Mock classification logic for offline development.
 * All values in GRAMS.
 */

import type { ClassResult, ClassBandCandidate } from '@/types/api';

interface ClassBand {
  class: string;
  eMin: number;
  eMax?: number;
  nMin: number;
  nMax: number;
  note?: string;
}

const CLASS_BANDS: ClassBand[] = [
  // Class I
  { class: 'I', eMin: 0.001, nMin: 50000, nMax: Infinity, note: 'e ≥ 0.001 g, n ≥ 50000' },
  
  // Class II
  { class: 'II', eMin: 0.001, eMax: 0.05, nMin: 100, nMax: 100000, note: '0.001 g ≤ e ≤ 0.05 g, 100 ≤ n ≤ 100000' },
  { class: 'II', eMin: 0.1, nMin: 5000, nMax: 100000, note: 'e ≥ 0.1 g, 5000 ≤ n ≤ 100000' },
  
  // Class III
  { class: 'III', eMin: 0.1, eMax: 2, nMin: 100, nMax: 10000, note: '0.1 g ≤ e ≤ 2 g, 100 ≤ n ≤ 10000' },
  { class: 'III', eMin: 5, nMin: 500, nMax: 10000, note: 'e ≥ 5 g, 500 ≤ n ≤ 10000' },
  
  // Class IIII
  { class: 'IIII', eMin: 5, nMin: 100, nMax: 1000, note: 'e ≥ 5 g, 100 ≤ n ≤ 1000' },
];

export function mockDetermineClass(eStr: string, maxCapacityStr: string): ClassResult {
  const e = parseFloat(eStr);
  const maxCapacity = parseFloat(maxCapacityStr);
  
  if (isNaN(e) || isNaN(maxCapacity) || e <= 0 || maxCapacity <= 0) {
    return {
      status: 'INVALID',
      computed_n: '0',
      class_: null,
      reason: 'Invalid input values',
    };
  }
  
  const n = maxCapacity / e;
  const computed_n_str = n.toFixed(0); // Plain number, no scientific notation
  
  const matches: ClassBandCandidate[] = [];
  
  for (const band of CLASS_BANDS) {
    const eInRange = e >= band.eMin && (!band.eMax || e <= band.eMax);
    const nInRange = n >= band.nMin && n <= band.nMax;
    
    if (eInRange && nInRange) {
      matches.push({
        class: band.class,
        e_range: band.eMax ? `${band.eMin} - ${band.eMax} g` : `≥ ${band.eMin} g`,
        n_range: band.nMax === Infinity ? `≥ ${band.nMin}` : `${band.nMin} - ${band.nMax}`,
        note: band.note,
      });
    }
  }
  
  if (matches.length === 0) {
    return {
      status: 'INVALID',
      computed_n: computed_n_str,
      class_: null,
      candidates: null,
      reason: `No class matches for e=${e} g, Max=${maxCapacity} g, n=${computed_n_str}`,
    };
  }
  
  if (matches.length === 1) {
    return {
      status: 'DETERMINED',
      computed_n: computed_n_str,
      class_: matches[0].class,
      candidates: null,
    };
  }
  
  return {
    status: 'AMBIGUOUS',
    computed_n: computed_n_str,
    class_: null,
    candidates: matches,
  };
}
