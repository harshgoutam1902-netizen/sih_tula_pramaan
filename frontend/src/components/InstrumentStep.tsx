import { useFormStore } from '../store/formStore';

interface Props {
  onNext: () => void;
}

export default function InstrumentStep({ onNext }: Props) {
  const { instrument, setInstrument } = useFormStore();
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Instrument Details</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Model
          </label>
          <input
            type="text"
            value={instrument.model}
            onChange={(e) => setInstrument({ model: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              e (verification scale interval, grams)
            </label>
            <input
              type="text"
              value={instrument.e}
              onChange={(e) => setInstrument({ e: e.target.value })}
              placeholder="0.001"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max (maximum capacity, grams)
            </label>
            <input
              type="text"
              value={instrument.max_capacity}
              onChange={(e) => setInstrument({ max_capacity: e.target.value })}
              placeholder="3000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>
        
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={instrument.is_electronic}
              onChange={(e) => setInstrument({ is_electronic: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">Electronic</span>
          </label>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Self-indicating Type
          </label>
          <select
            value={instrument.self_indicating_type}
            onChange={(e) => setInstrument({ self_indicating_type: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="self_indicating">Self-indicating</option>
            <option value="semi_self_indicating">Semi self-indicating</option>
            <option value="non_self_indicating">Non self-indicating</option>
          </select>
        </div>
        
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={instrument.has_tare_device}
              onChange={(e) => setInstrument({ has_tare_device: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">Has tare device</span>
          </label>
        </div>
        
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">All values in grams</p>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Next
          </button>
        </div>
      </form>
    </div>
  );
}
