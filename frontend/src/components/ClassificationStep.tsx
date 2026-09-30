import { useState, useEffect } from 'react';
import { useFormStore } from '../store/formStore';
import { mockDetermineClass } from '../lib/mockClassification';
import { classificationApi } from '../lib/api/classification';
import { ragApi } from '../lib/api/rag';
import { mockExplainClass } from '../lib/mockRag';
import AdvisoryBadge from './AdvisoryBadge';
import CitationList from './CitationList';
import type { ClassExplanationResponse } from '../lib/api/rag';

interface Props {
  onNext: () => void;
}

export default function ClassificationStep({ onNext }: Props) {
  const {
    instrument,
    classification,
    confirmedClass,
    confirmedBy,
    overrideReason,
    setClassification,
    setConfirmedClass,
    setConfirmedBy,
    setOverrideReason,
    setBackendOnline,
  } = useFormStore();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ClassExplanationResponse | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  
  const handleDetermineClass = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Try real backend first
      try {
        const result = await classificationApi.determine({
          e: instrument.e,
          max_capacity: instrument.max_capacity,
          rulepack_version: 'R76-1:2006',
        });
        setClassification(result);
        setBackendOnline(true);
      } catch (err) {
        // Fall back to mock
        console.log('Backend unavailable, using mock');
        const result = mockDetermineClass(instrument.e, instrument.max_capacity);
        setClassification(result);
        setBackendOnline(false);
      }
    } catch (err) {
      setError('Failed to determine class');
    } finally {
      setLoading(false);
    }
  };
  
  const canConfirm = classification && 
    (classification.status === 'AMBIGUOUS' || classification.status === 'INVALID') &&
    confirmedClass &&
    confirmedBy.trim().length > 0;
  
  const isConfirmed = classification?.status === 'DETERMINED' || confirmedClass !== null;
  
  const effectiveClass = classification?.class_ || confirmedClass;
  
  // Fetch explanation when class is determined or confirmed
  useEffect(() => {
    if (effectiveClass && !loadingExplanation) {
      setLoadingExplanation(true);
      setExplanation(null);
      
      ragApi
        .explainClass(effectiveClass, 3)
        .then((data) => {
          setExplanation(data);
        })
        .catch(() => {
          // Fall back to mock
          const mockData = mockExplainClass(effectiveClass, 3);
          setExplanation(mockData);
        })
        .finally(() => {
          setLoadingExplanation(false);
        });
    }
  }, [effectiveClass, loadingExplanation]);
  
  return (
    <div className="space-y-6 max-w-2xl">
      {/* Determine Button */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">e = {instrument.e} g</p>
            <p className="text-sm text-gray-600">Max = {instrument.max_capacity} g</p>
          </div>
          <button
            onClick={handleDetermineClass}
            disabled={loading || !instrument.e || !instrument.max_capacity}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {loading ? 'Determining...' : 'Determine Class'}
          </button>
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>
      
      {/* Classification Result */}
      {classification && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Classification Result</h3>
            <span
              className={`px-3 py-1 text-sm font-semibold rounded ${
                classification.status === 'DETERMINED'
                  ? 'bg-green-100 text-green-800'
                  : classification.status === 'AMBIGUOUS'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {classification.status}
            </span>
          </div>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium text-gray-700">Computed n:</p>
              <p className="text-lg font-mono">{classification.computed_n}</p>
            </div>
            
            {classification.status === 'DETERMINED' && classification.class_ && (
              <div>
                <p className="text-sm font-medium text-gray-700">Class:</p>
                <p className="text-2xl font-bold text-green-700">Class {classification.class_}</p>
              </div>
            )}
            
            {classification.status === 'AMBIGUOUS' && classification.candidates && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Candidate Classes:</p>
                <div className="space-y-2">
                  {classification.candidates.map((candidate, idx) => (
                    <label
                      key={idx}
                      className="flex items-start space-x-3 p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="class"
                        value={candidate.class}
                        checked={confirmedClass === candidate.class}
                        onChange={(e) => setConfirmedClass(e.target.value)}
                        className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">Class {candidate.class}</p>
                        <p className="text-xs text-gray-600">e: {candidate.e_range}</p>
                        <p className="text-xs text-gray-600">n: {candidate.n_range}</p>
                        {candidate.note && (
                          <p className="text-xs text-gray-500 mt-1">{candidate.note}</p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {classification.status === 'INVALID' && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Override Class:</p>
                <select
                  value={confirmedClass || ''}
                  onChange={(e) => setConfirmedClass(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select class...</option>
                  <option value="I">Class I</option>
                  <option value="II">Class II</option>
                  <option value="III">Class III</option>
                  <option value="IIII">Class IIII</option>
                </select>
                {classification.reason && (
                  <p className="mt-2 text-sm text-red-600">{classification.reason}</p>
                )}
              </div>
            )}
            
            {(classification.status === 'AMBIGUOUS' || classification.status === 'INVALID') && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirmed by (required)
                  </label>
                  <input
                    type="text"
                    value={confirmedBy}
                    onChange={(e) => setConfirmedBy(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason (optional)
                  </label>
                  <textarea
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    placeholder="Enter reason for override..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <button
                  onClick={() => {
                    if (canConfirm) {
                      // Just mark as confirmed - real app would call API
                      alert(`Class ${confirmedClass} confirmed by ${confirmedBy}`);
                    }
                  }}
                  disabled={!canConfirm}
                  className="w-full px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Confirm Classification
                </button>
              </>
            )}
          </div>
        </div>
      )}
      
      {/* Why? Panel */}
      {effectiveClass && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Why?</h3>
            <AdvisoryBadge />
          </div>
          
          {loadingExplanation ? (
            <p className="text-sm text-gray-500">Loading explanation...</p>
          ) : explanation ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Class {explanation.accuracy_class}
                </p>
                <p className="text-sm text-gray-800">{explanation.explanation}</p>
              </div>
              
              {classification?.status === 'AMBIGUOUS' && classification.candidates && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    What distinguishes the candidates:
                  </p>
                  <div className="space-y-2 text-sm text-gray-700">
                    {classification.candidates.map((candidate, idx) => (
                      <div key={idx} className="pl-4 border-l-2 border-gray-300">
                        <p className="font-semibold">Class {candidate.class}</p>
                        <p className="text-xs text-gray-600">e: {candidate.e_range}</p>
                        <p className="text-xs text-gray-600">n: {candidate.n_range}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {explanation.relevant_clauses.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Relevant clauses:
                  </p>
                  <CitationList clauses={explanation.relevant_clauses} />
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
      
      {/* Next Button */}
      {isConfirmed && (
        <div className="flex justify-end">
          <button
            onClick={onNext}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
