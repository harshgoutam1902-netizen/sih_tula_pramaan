import type { ClauseResult } from '../lib/api/rag';

interface Props {
  clauses: ClauseResult[];
  showScores?: boolean;
}

export default function CitationList({ clauses, showScores = false }: Props) {
  return (
    <div className="space-y-3">
      {clauses.map((clause) => (
        <div key={clause.id} className="border border-gray-200 rounded-md p-3 bg-gray-50">
          <div className="flex items-start justify-between mb-2">
            <div>
              <span className="text-xs font-semibold text-blue-700">
                {clause.id}
              </span>
              <p className="text-xs text-gray-600 mt-0.5">{clause.source}</p>
            </div>
            {showScores && (
              <span className="text-xs font-mono text-gray-500">
                {clause.score.toFixed(3)}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-800">{clause.text}</p>
        </div>
      ))}
    </div>
  );
}
