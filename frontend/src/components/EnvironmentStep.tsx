import { useState, useEffect, useCallback } from 'react';
import { useFormStore } from '../store/formStore';
import { ragApi } from '../lib/api/rag';
import { mlApi } from '../lib/api/ml';
import { mockQueryClauses } from '../lib/mockRag';
import { mockDriftRisk } from '../lib/mockDrift';
import AdvisoryBadge from './AdvisoryBadge';
import CitationList from './CitationList';
import type { RAGQueryResponse } from '../lib/api/rag';

export default function EnvironmentStep() {
  const { environment, readings, setEnvironment, addReading, updateReading, backendOnline } = useFormStore();
  
  const [query, setQuery] = useState('');
  const [ragResults, setRagResults] = useState<RAGQueryResponse | null>(null);
  const [loadingRag, setLoadingRag] = useState(false);
  const [driftBackendOnline, setDriftBackendOnline] = useState(true);
  
  const handleAddReading = (e: React.FormEvent) => {
    e.preventDefault();
    
    const lastReading = readings[readings.length - 1];
    
    addReading({
      checkpoint: readings.length === 0 ? 'start' : readings.length === 1 ? 'max' : 'end',
      temp: lastReading ? lastReading.temp : environment.temp,
      humidity: lastReading ? lastReading.humidity : environment.humidity,
      pressure: lastReading ? lastReading.pressure : environment.pressure,
      source: lastReading ? 'auto' : 'override',
    });
  };
  
  const handleOverride = (id: string) => {
    const reading = readings.find((r) => r.id === id);
    if (!reading) return;
    
    const newTemp = prompt('Enter temperature (°C):', reading.temp);
    const newHumidity = prompt('Enter humidity (%):', reading.humidity);
    const newPressure = prompt('Enter pressure (kPa):', reading.pressure);
    
    if (newTemp && newHumidity && newPressure) {
      updateReading(id, {
        temp: newTemp,
        humidity: newHumidity,
        pressure: newPressure,
        source: 'override',
      });
    }
  };
  
  const handleAskStandard = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setLoadingRag(true);
    
    try {
      const result = await ragApi.query(query, 3);
      setRagResults(result);
    } catch (err) {
      // Fall back to mock
      const mockResult = mockQueryClauses(query, 3);
      setRagResults(mockResult);
    } finally {
      setLoadingRag(false);
    }
  };
  
  // Calculate drift risks (debounced)
  const calculateDriftRisks = useCallback(async () => {
    if (readings.length === 0) return;
    
    const baseline = readings[0];
    const baselineTemp = parseFloat(baseline.temp);
    const baselineRh = parseFloat(baseline.humidity);
    
    if (isNaN(baselineTemp) || isNaN(baselineRh)) return;
    
    try {
      const response = await mlApi.predictDriftRisk({
        baseline: { temp: baselineTemp, rh: baselineRh },
        readings: readings.map(r => ({
          temp: parseFloat(r.temp) || 0,
          rh: parseFloat(r.humidity) || 0,
          load_pct: 50,
          time_spanning: 1,
        })),
      });
      
      // Update readings with risks
      readings.forEach((reading, idx) => {
        if (response.risks[idx] !== undefined) {
          updateReading(reading.id, { risk: response.risks[idx] });
        }
      });
      
      setDriftBackendOnline(true);
    } catch (err) {
      // Fall back to mock
      readings.forEach((reading) => {
        const temp = parseFloat(reading.temp) || 0;
        const rh = parseFloat(reading.humidity) || 0;
        const deltaTemp = temp - baselineTemp;
        const deltaRh = rh - baselineRh;
        const risk = mockDriftRisk(deltaTemp, deltaRh, 50, 1);
        updateReading(reading.id, { risk });
      });
      
      setDriftBackendOnline(false);
    }
  }, [readings, updateReading]);
  
  // Debounced drift calculation
  useEffect(() => {
    const timer = setTimeout(() => {
      calculateDriftRisks();
    }, 200);
    
    return () => clearTimeout(timer);
  }, [calculateDriftRisks]);
  
  return (
    <div className="space-y-6 max-w-4xl">
      {/* Environment Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Environment Parameters</h3>
        
        <form onSubmit={handleAddReading} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature (°C)
              </label>
              <input
                type="text"
                value={environment.temp}
                onChange={(e) => setEnvironment({ temp: e.target.value })}
                placeholder="23.0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Humidity (%)
              </label>
              <input
                type="text"
                value={environment.humidity}
                onChange={(e) => setEnvironment({ humidity: e.target.value })}
                placeholder="50"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pressure (kPa)
              </label>
              <input
                type="text"
                value={environment.pressure}
                onChange={(e) => setEnvironment({ pressure: e.target.value })}
                placeholder="101.3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add Reading
          </button>
        </form>
      </div>
      
      {/* Readings Table */}
      {readings.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Environment Readings</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Checkpoint
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Temp (°C)
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Humidity (%)
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pressure (kPa)
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk (demo model)
                    {!driftBackendOnline && (
                      <span className="ml-2 px-1 py-0.5 text-xs font-medium bg-gray-200 text-gray-700 rounded">
                        offline
                      </span>
                    )}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {readings.map((reading) => {
                  const risk = reading.risk ?? 0;
                  const riskColor = risk < 0.33 ? 'bg-green-500' : risk < 0.66 ? 'bg-amber-500' : 'bg-red-500';
                  
                  return (
                    <tr key={reading.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {reading.checkpoint}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {reading.temp}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {reading.humidity}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {reading.pressure}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            reading.source === 'auto'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-purple-100 text-purple-800'
                          }`}
                        >
                          {reading.source}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-4 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${riskColor}`}
                              style={{ width: `${risk * 100}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono text-gray-600">
                            {risk.toFixed(3)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleOverride(reading.id)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Override
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Ask the Standard */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Ask the Standard</h3>
          <div className="flex items-center gap-2">
            <AdvisoryBadge />
            {!backendOnline && (
              <span className="px-2 py-1 text-xs font-medium bg-gray-200 text-gray-700 rounded">
                Offline Mock
              </span>
            )}
          </div>
        </div>
        
        <form onSubmit={handleAskStandard} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What are the environment recording requirements?"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button
            type="submit"
            disabled={loadingRag || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {loadingRag ? 'Searching...' : 'Ask'}
          </button>
        </form>
        
        {ragResults && ragResults.results.length > 0 && (
          <div className="mt-6">
            <p className="text-sm font-medium text-gray-700 mb-3">
              Top 3 Citations:
            </p>
            <CitationList clauses={ragResults.results} showScores={true} />
          </div>
        )}
      </div>
    </div>
  );
}
