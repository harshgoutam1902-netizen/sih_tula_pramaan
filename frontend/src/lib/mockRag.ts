/**
 * Mock RAG service for offline development.
 */

import type { RAGQueryResponse, ClassExplanationResponse } from './api/rag';

const MOCK_CLAUSES: Array<{ id: string; source: string; text: string; keywords: string[] }> = [
  {
    id: '3.1.2',
    source: 'OIML R76-1:2006 Section 3.1.2',
    text: 'The verification scale interval e is the value expressed in units of mass used for classification and verification of the instrument. The number of verification scale intervals n equals Max divided by e.',
    keywords: ['verification', 'scale', 'interval', 'e', 'n', 'max', 'classification'],
  },
  {
    id: '3.4.1',
    source: 'OIML R76-1:2006 Table 3',
    text: 'Class I instruments require e greater than or equal to 0.001 grams and n greater than or equal to 50000. Used for precision balances in laboratory settings.',
    keywords: ['class', 'i', 'precision', 'laboratory', '0.001', '50000'],
  },
  {
    id: '3.4.2',
    source: 'OIML R76-1:2006 Table 3',
    text: 'Class II instruments have two bands: e between 0.001 and 0.05 grams with n between 100 and 100000, or e greater than or equal to 0.1 grams with n between 5000 and 100000. Used for precision weighing in trade.',
    keywords: ['class', 'ii', 'trade', 'precision', '0.001', '0.05', '0.1', '100', '100000', '5000'],
  },
  {
    id: '3.4.3',
    source: 'OIML R76-1:2006 Table 3',
    text: 'Class III instruments have two bands: e between 0.1 and 2 grams with n between 100 and 10000, or e greater than or equal to 5 grams with n between 500 and 10000. Most common for commercial weighing.',
    keywords: ['class', 'iii', 'commercial', 'weighing', '0.1', '2', '5', '100', '10000', '500'],
  },
  {
    id: '3.4.4',
    source: 'OIML R76-1:2006 Table 3',
    text: 'Class IIII instruments require e greater than or equal to 5 grams with n between 100 and 1000. Used for rough industrial weighing applications.',
    keywords: ['class', 'iiii', 'industrial', 'rough', '5', '100', '1000'],
  },
  {
    id: '4.1.1',
    source: 'OIML R76-1:2006 Section 4.1',
    text: 'Environmental conditions during testing must be recorded including temperature in degrees Celsius, relative humidity as percentage, and barometric pressure in kilopascals. Ambient temperature should be between 15 and 30 degrees Celsius.',
    keywords: ['environment', 'temperature', 'humidity', 'pressure', 'testing', 'recording', 'celsius', 'kilopascals'],
  },
  {
    id: '4.2.1',
    source: 'OIML R76-1:2006 Section 4.2',
    text: 'Repeatability testing requires at least six identical load applications at the same load point. The difference between maximum and minimum readings must not exceed the MPE for that load.',
    keywords: ['repeatability', 'test', 'load', 'mpe', 'six'],
  },
  {
    id: '4.10.1',
    source: 'OIML R76-1:2006 Section 4.10',
    text: 'Electronic instruments must undergo environmental testing including damp heat cyclic conditions. The instrument is subjected to temperature and humidity cycles per specified profiles.',
    keywords: ['electronic', 'environmental', 'testing', 'damp', 'heat', 'temperature', 'humidity', 'cycles'],
  },
];

function scoreClause(query: string, clause: { keywords: string[] }): number {
  const queryWords = query.toLowerCase().split(/\s+/);
  let matches = 0;
  
  for (const word of queryWords) {
    if (clause.keywords.some(kw => kw.includes(word) || word.includes(kw))) {
      matches++;
    }
  }
  
  return matches / Math.max(queryWords.length, 1);
}

export function mockQueryClauses(query: string, k: number = 3): RAGQueryResponse {
  const scored = MOCK_CLAUSES.map(clause => ({
    id: clause.id,
    source: clause.source,
    text: clause.text,
    score: scoreClause(query, clause),
  }));
  
  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.id.localeCompare(b.id);
  });
  
  return {
    results: scored.slice(0, k),
    advisory_only: true,
    draft: true,
  };
}

const CLASS_EXPLANATIONS: Record<string, string> = {
  I: 'Class I instruments are high-precision balances used in laboratory settings. They require e ≥ 0.001 grams and n ≥ 50,000 verification intervals.',
  II: 'Class II instruments are precision weighing devices used in trade. They have two specification bands: e between 0.001-0.05 g with n between 100-100,000, or e ≥ 0.1 g with n between 5,000-100,000.',
  III: 'Class III instruments are the most common commercial weighing devices. They have two bands: e between 0.1-2 g with n between 100-10,000, or e ≥ 5 g with n between 500-10,000.',
  IIII: 'Class IIII instruments are rough industrial weighing devices. They require e ≥ 5 grams with n between 100-1,000 verification intervals.',
};

export function mockExplainClass(accuracyClass: string, k: number = 3): ClassExplanationResponse {
  const cls = accuracyClass.toUpperCase();
  const query = `class ${cls} requirements`;
  const queryResult = mockQueryClauses(query, k);
  
  return {
    accuracy_class: cls,
    explanation: CLASS_EXPLANATIONS[cls] || 'Unknown accuracy class',
    relevant_clauses: queryResult.results,
    advisory_only: true,
    draft: true,
  };
}
