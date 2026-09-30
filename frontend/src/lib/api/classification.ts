/**
 * Classification API endpoints.
 */

import apiClient from './client';
import type {
  DetermineClassRequest,
  ClassResult,
  ConfirmClassificationRequest,
  ConfirmClassificationResponse,
} from '@/types/api';

export const classificationApi = {
  /**
   * Determine accuracy class from e and Max capacity.
   */
  async determine(request: DetermineClassRequest): Promise<ClassResult> {
    const response = await apiClient.post<ClassResult>(
      '/classification/determine',
      request
    );
    return response.data;
  },

  /**
   * Confirm classification with human validation.
   */
  async confirm(
    request: ConfirmClassificationRequest
  ): Promise<ConfirmClassificationResponse> {
    const response = await apiClient.post<ConfirmClassificationResponse>(
      '/classification/confirm',
      request
    );
    return response.data;
  },

  /**
   * Get suggested minimum capacity for given e and class.
   */
  async suggestMin(
    e: string,
    accuracyClass: string,
    rulepackVersion: string = 'R76-1:2006'
  ): Promise<{
    e: string;
    accuracy_class: string;
    suggested_min_capacity: string;
    unit: string;
    note: string;
  }> {
    const response = await apiClient.get(
      `/classification/suggest-min/${e}/${accuracyClass}`,
      {
        params: { rulepack_version: rulepackVersion },
      }
    );
    return response.data;
  },

  /**
   * Get classification history for an instrument.
   */
  async getHistory(instrumentProfileId: number): Promise<any[]> {
    const response = await apiClient.get(
      `/classification/history/${instrumentProfileId}`
    );
    return response.data;
  },
};
