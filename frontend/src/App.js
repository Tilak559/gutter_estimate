import React, { useState } from 'react';
import AddressForm from './components/AddressForm';
import ResultsDisplay from './components/ResultsDisplay';
import Header from './components/Header';
import { MapPin, Home, Calculator, Image as ImageIcon } from 'lucide-react';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleEstimate = async (address) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`/api/v1/classify-roof?address=${encodeURIComponent(address)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        console.log('API Response:', data);
        setResults(data);
      } else {
        throw new Error(data.error || 'Failed to get estimate');
      }
    } catch (err) {
      setError(err.message);
      console.error('Estimation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-primary-500 p-4 rounded-full">
              <Home className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            AI-Powered Gutter Estimation
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Get accurate gutter estimates for any address using advanced AI analysis of satellite imagery and building data.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
            <MapPin className="h-12 w-12 text-primary-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Address Input</h3>
            <p className="text-gray-600">Simply enter any address and our system will analyze the property</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
            <ImageIcon className="h-12 w-12 text-primary-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Satellite Analysis</h3>
            <p className="text-gray-600">AI-powered analysis of high-resolution satellite imagery</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
            <Calculator className="h-12 w-12 text-primary-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Accurate Estimates</h3>
            <p className="text-gray-600">Get precise gutter length estimates with detailed breakdowns</p>
          </div>
        </div>

        {/* Main Form */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 mb-8">
          <AddressForm onSubmit={handleEstimate} loading={loading} />
        </div>

        {/* Results Display */}
        {loading && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Analyzing Property</h3>
            <p className="text-gray-600">Our AI is processing satellite imagery and building data<span className="loading-dots"></span></p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
            <div className="text-red-600 mb-4">
              <svg className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-red-900 mb-2">Estimation Failed</h3>
            <p className="text-red-700">{error}</p>
            <button 
              onClick={() => setError(null)}
              className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {results && !loading && (
          <ResultsDisplay results={results} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-400">
            © 2025 Gutter Estimate. Powered by Leashed AI.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
