/**
 * ML API endpoints for drift risk model.
 * DEMO only - hardcoded weights, not learned, never decides anything regulatory.
 */

import apiClient from './client';

export interface BaselineReading {
  temp: number;
  rh: number;
}

export interface DriftReading {
  temp: number;
  rh: number;
  load_pct?: number;
  time_spanning?: number;
}

export interface DriftRiskRequest {
  baseline: BaselineReading;
  readings: DriftReading[];
}

export interface DriftRiskResponse {
  risks: number[];
  model_version: string;
  demo: boolean;
  draft: boolean;
}

export const mlApi = {
  /**
   * Predict drift risk for environmental readings.
   */
  async predictDriftRisk(request: DriftRiskRequest): Promise<DriftRiskResponse> {
    const response = await apiClient.post<DriftRiskResponse>(
      '/ml/drift-risk',
      request
    );
    return response.data;
  },
};
