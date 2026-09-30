/**
 * Zustand store for 3-stage form state.
 */

import { create } from 'zustand';
import type { ClassResult, ResolvedTest } from '@/types/api';

interface InstrumentForm {
  model: string;
  e: string;
  max_capacity: string;
  is_electronic: boolean;
  self_indicating_type: 'self_indicating' | 'semi_self_indicating' | 'non_self_indicating';
  has_tare_device: boolean;
}

interface EnvironmentReading {
  id: string;
  checkpoint: 'start' | 'max' | 'end';
  temp: string;
  humidity: string;
  pressure: string;
  source: 'auto' | 'override';
  risk?: number;
}

interface EnvironmentForm {
  temp: string;
  humidity: string;
  pressure: string;
}

interface FormState {
  // Step 1: Instrument
  instrument: InstrumentForm;
  setInstrument: (data: Partial<InstrumentForm>) => void;
  
  // Step 2: Classification
  classification: ClassResult | null;
  confirmedClass: string | null;
  confirmedBy: string;
  overrideReason: string;
  setClassification: (result: ClassResult) => void;
  setConfirmedClass: (className: string) => void;
  setConfirmedBy: (name: string) => void;
  setOverrideReason: (reason: string) => void;
  
  // Step 3: Test Plan
  testPlan: ResolvedTest[];
  setTestPlan: (tests: ResolvedTest[]) => void;
  
  // Step 4: Environment
  environment: EnvironmentForm;
  readings: EnvironmentReading[];
  setEnvironment: (data: Partial<EnvironmentForm>) => void;
  addReading: (reading: Omit<EnvironmentReading, 'id'>) => void;
  updateReading: (id: string, data: Partial<EnvironmentReading>) => void;
  
  // Backend status
  backendOnline: boolean;
  setBackendOnline: (online: boolean) => void;
  
  // Reset
  reset: () => void;
}

const initialInstrument: InstrumentForm = {
  model: '',
  e: '',
  max_capacity: '',
  is_electronic: false,
  self_indicating_type: 'self_indicating',
  has_tare_device: false,
};

const initialEnvironment: EnvironmentForm = {
  temp: '',
  humidity: '',
  pressure: '',
};

export const useFormStore = create<FormState>((set) => ({
  instrument: initialInstrument,
  setInstrument: (data) => set((state) => ({ instrument: { ...state.instrument, ...data } })),
  
  classification: null,
  confirmedClass: null,
  confirmedBy: '',
  overrideReason: '',
  setClassification: (result) => set({ 
    classification: result,
    confirmedClass: result.status === 'DETERMINED' ? result.class_ || null : null,
  }),
  setConfirmedClass: (className) => set({ confirmedClass: className }),
  setConfirmedBy: (name) => set({ confirmedBy: name }),
  setOverrideReason: (reason) => set({ overrideReason: reason }),
  
  testPlan: [],
  setTestPlan: (tests) => set({ testPlan: tests }),
  
  environment: initialEnvironment,
  readings: [],
  setEnvironment: (data) => set((state) => ({ environment: { ...state.environment, ...data } })),
  addReading: (reading) => set((state) => ({
    readings: [...state.readings, { ...reading, id: `reading-${Date.now()}` }],
  })),
  updateReading: (id, data) => set((state) => ({
    readings: state.readings.map((r) => r.id === id ? { ...r, ...data } : r),
  })),
  
  backendOnline: false,
  setBackendOnline: (online) => set({ backendOnline: online }),
  
  reset: () => set({
    instrument: initialInstrument,
    classification: null,
    confirmedClass: null,
    confirmedBy: '',
    overrideReason: '',
    testPlan: [],
    environment: initialEnvironment,
    readings: [],
  }),
}));
