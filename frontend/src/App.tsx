import { useState } from 'react';
import { useFormStore } from './store/formStore';
import InstrumentStep from './components/InstrumentStep';
import ClassificationStep from './components/ClassificationStep';
import TestPlanStep from './components/TestPlanStep';
import EnvironmentStep from './components/EnvironmentStep';

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const { classification, confirmedClass, backendOnline } = useFormStore();
  
  const isClassConfirmed = classification?.status === 'DETERMINED' || confirmedClass !== null;
  
  const steps = [
    { num: 1, name: 'Instrument', enabled: true },
    { num: 2, name: 'Classification', enabled: true },
    { num: 3, name: 'Test Plan', enabled: isClassConfirmed },
    { num: 4, name: 'Environment', enabled: isClassConfirmed },
  ];
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">TulaPramaan</h1>
              <span className="px-2 py-1 text-xs font-semibold bg-yellow-100 text-yellow-800 rounded">
                DRAFT
              </span>
            </div>
            {!backendOnline && (
              <span className="px-2 py-1 text-xs font-medium bg-gray-200 text-gray-700 rounded">
                Offline Mock
              </span>
            )}
          </div>
        </div>
      </header>
      
      {/* Step Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {steps.map((step) => (
              <button
                key={step.num}
                onClick={() => step.enabled && setCurrentStep(step.num)}
                disabled={!step.enabled}
                className={`
                  py-4 px-2 border-b-2 font-medium text-sm transition-colors
                  ${currentStep === step.num
                    ? 'border-blue-500 text-blue-600'
                    : step.enabled
                    ? 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    : 'border-transparent text-gray-300 cursor-not-allowed'
                  }
                `}
              >
                {step.num}. {step.name}
              </button>
            ))}
          </div>
        </div>
      </nav>
      
      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentStep === 1 && <InstrumentStep onNext={() => setCurrentStep(2)} />}
        {currentStep === 2 && <ClassificationStep onNext={() => setCurrentStep(3)} />}
        {currentStep === 3 && <TestPlanStep onNext={() => setCurrentStep(4)} />}
        {currentStep === 4 && <EnvironmentStep />}
      </main>
    </div>
  );
}

export default App;
