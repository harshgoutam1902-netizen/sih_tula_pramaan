import { useEffect } from 'react';
import { useFormStore } from '../store/formStore';
import { mockGenerateTestPlan } from '../lib/mockTestPlan';

interface Props {
  onNext: () => void;
}

export default function TestPlanStep({ onNext }: Props) {
  const { instrument, classification, confirmedClass, testPlan, setTestPlan } = useFormStore();
  
  const finalClass = classification?.class_ || confirmedClass || '';
  
  useEffect(() => {
    if (finalClass && testPlan.length === 0) {
      const tests = mockGenerateTestPlan({
        class_: finalClass,
        is_electronic: instrument.is_electronic,
        self_indicating_type: instrument.self_indicating_type,
        has_tare_device: instrument.has_tare_device,
      });
      setTestPlan(tests);
    }
  }, [finalClass, testPlan.length, instrument, setTestPlan]);
  
  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Test Plan</h3>
          <span className="text-sm text-gray-600">
            Class {finalClass} • {testPlan.length} tests
          </span>
        </div>
        
        {testPlan.length === 0 ? (
          <p className="text-gray-500">Loading test plan...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    #
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Test Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {testPlan.map((test, idx) => (
                  <tr key={test.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {idx + 1}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {test.name}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          test.duration_category === 'short'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-orange-100 text-orange-800'
                        }`}
                      >
                        {test.duration_category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {test.resolved_variant || 'Required for all instruments'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Short tests:</p>
              <p className="font-semibold text-gray-900">
                {testPlan.filter((t) => t.duration_category === 'short').length}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Time-spanning tests:</p>
              <p className="font-semibold text-gray-900">
                {testPlan.filter((t) => t.duration_category === 'time_spanning').length}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex justify-end">
        <button
          onClick={onNext}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Next
        </button>
      </div>
    </div>
  );
}
