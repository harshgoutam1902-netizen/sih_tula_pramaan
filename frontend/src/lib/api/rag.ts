/**
 * RAG (Retrieval Augmented Generation) API endpoints.
 */

import apiClient from './client';

export interface ClauseResult {
  id: string;
  source: string;
  text: string;
  score: number;
}

export interface RAGQueryResponse {
  results: ClauseResult[];
  advisory_only: boolean;
  draft: boolean;
}

export interface ClassExplanationResponse {
  accuracy_class: string;
  explanation: string;
  relevant_clauses: ClauseResult[];
  advisory_only: boolean;
  draft: boolean;
}

export const ragApi = {
  /**
   * Query clauses with natural language.
   */
  async query(query: string, k: number = 3): Promise<RAGQueryResponse> {
    const response = await apiClient.post<RAGQueryResponse>(
      '/rag/query',
      { query, k }
    );
    return response.data;
  },

  /**
   * Get explanation for an accuracy class.
   */
  async explainClass(accuracyClass: string, k: number = 3): Promise<ClassExplanationResponse> {
    const response = await apiClient.get<ClassExplanationResponse>(
      `/rag/explain-class/${accuracyClass}`,
      { params: { k } }
    );
    return response.data;
  },
};
