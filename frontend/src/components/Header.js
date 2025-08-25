import React from 'react';
import { Home, MapPin, BarChart3 } from 'lucide-react';

function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-100">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-500 p-2 rounded-lg">
              <Home className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Gutter Estimate</h1>
              <p className="text-sm text-gray-600">AI-Powered Estimation System</p>
            </div>
          </div>
          
          {/* <nav className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-600 hover:text-primary-600 transition-colors flex items-center space-x-2">
              <MapPin className="h-4 w-4" />
              <span>Features</span>
            </a>
            <a href="#about" className="text-gray-600 hover:text-primary-600 transition-colors flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>About</span>
            </a>
          </nav> */}
          
          <div className="md:hidden">
            <button className="p-2 text-gray-600 hover:text-primary-600 transition-colors">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
