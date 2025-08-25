import React, { useState } from 'react';
import { MapPin, Search, ArrowRight } from 'lucide-react';

function AddressForm({ onSubmit, loading }) {
  const [address, setAddress] = useState('');
  const [isValid, setIsValid] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!address.trim()) {
      setIsValid(false);
      return;
    }
    
    setIsValid(true);
    onSubmit(address.trim());
  };

  const handleAddressChange = (e) => {
    setAddress(e.target.value);
    if (e.target.value.trim()) {
      setIsValid(true);
    }
  };

  return (
    <div>
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <div className="bg-primary-100 p-3 rounded-full">
            <MapPin className="h-8 w-8 text-primary-600" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          Get Your Gutter Estimate
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Enter any address below and our AI will analyze satellite imagery to provide an accurate gutter estimate.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={address}
            onChange={handleAddressChange}
            placeholder="Enter full address (e.g., 123 Main St, City, State 12345)"
            className={`w-full pl-12 pr-4 py-4 text-lg border-2 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 transition-all ${
              isValid 
                ? 'border-gray-200 focus:border-primary-500' 
                : 'border-red-300 focus:border-red-500 focus:ring-red-100'
            }`}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className={`absolute right-2 top-2 p-2 rounded-lg transition-all ${
              loading || !address.trim()
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-500 text-white hover:bg-primary-600 hover:scale-105'
            }`}
          >
            <ArrowRight className="h-5 w-5" />
          </button>
        </div>
        
        {!isValid && (
          <p className="text-red-600 text-sm mt-2 text-center">
            Please enter a valid address
          </p>
        )}

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            💡 <strong>Tip:</strong> Include city and state for best results
          </p>
        </div>
      </form>

      {/* Example Addresses */}
      <div className="mt-8 text-center">
        <p className="text-sm text-gray-500 mb-3">Try these example addresses:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {[
            '28 Cragswood Road, New Paltz, NY 12561',
            '508 Washington Avenue, Beacon, NY 12508',
            '4 Pattie Pl, Wappingers Falls, NY 12590',
            '28 Cragswood Road, New Paltz, NY 12561',
            '14 Hideaway Ln Newburgh, NY 12550'

          ].map((example, index) => (
            <button
              key={index}
              onClick={() => setAddress(example)}
              disabled={loading}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AddressForm;
