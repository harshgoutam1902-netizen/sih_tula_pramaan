/**
 * Environment API endpoints.
 */

import apiClient from './client';
import type {
  CreateEnvironmentSessionRequest,
  EnvironmentSession,
  OverrideEnvironmentReadingRequest,
  EnvironmentReading,
  EnvironmentSummary,
} from '@/types/api';

export const environmentApi = {
  /**
   * Create environment session.
   */
  async createSession(
    request: CreateEnvironmentSessionRequest
  ): Promise<{ environment_session_id: number; message: string }> {
    const response = await apiClient.post('/environment/session', request);
    return response.data;
  },

  /**
   * Get environment session.
   */
  async getSession(testJobId: number): Promise<EnvironmentSession> {
    const response = await apiClient.get<EnvironmentSession>(
      `/environment/session/${testJobId}`
    );
    return response.data;
  },

  /**
   * Override environment reading for a checkpoint.
   */
  async overrideReading(
    request: OverrideEnvironmentReadingRequest
  ): Promise<{ environment_reading_id: number; source: string; message: string }> {
    const response = await apiClient.post(
      '/environment/reading/override',
      request
    );
    return response.data;
  },

  /**
   * Get all environment readings for a test run.
   */
  async getReadings(testRunId: number): Promise<EnvironmentReading[]> {
    const response = await apiClient.get<EnvironmentReading[]>(
      `/environment/readings/${testRunId}`
    );
    return response.data;
  },

  /**
   * Get consolidated environment summary for final report.
   */
  async getSummary(testJobId: number): Promise<EnvironmentSummary> {
    const response = await apiClient.get<EnvironmentSummary>(
      `/environment/summary/${testJobId}`
    );
    return response.data;
  },
};
