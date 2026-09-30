/**
 * Test plan API endpoints.
 */

import apiClient from './client';
import type {
  AssembleTestPlanRequest,
  AssembleTestPlanResponse,
  TestPlan,
  TestPlanSummary,
} from '@/types/api';

export const testPlansApi = {
  /**
   * Assemble test plan from confirmed classification.
   */
  async assemble(
    request: AssembleTestPlanRequest
  ): Promise<AssembleTestPlanResponse> {
    const response = await apiClient.post<AssembleTestPlanResponse>(
      '/test-plans/assemble',
      request
    );
    return response.data;
  },

  /**
   * Retrieve existing test plan.
   */
  async get(testJobId: number): Promise<TestPlan & { id: number; test_job_id: number }> {
    const response = await apiClient.get(`/test-plans/${testJobId}`);
    return response.data;
  },

  /**
   * Get test plan summary statistics.
   */
  async getSummary(testJobId: number): Promise<TestPlanSummary> {
    const response = await apiClient.get<TestPlanSummary>(
      `/test-plans/${testJobId}/summary`
    );
    return response.data;
  },
};
