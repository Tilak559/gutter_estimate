import React, { useState } from 'react';
import { 
  MapPin, 
  Home, 
  Ruler, 
  Image as ImageIcon, 
  Info, 
  AlertTriangle,
  Download,
  Eye
} from 'lucide-react';

function ResultsDisplay({ results }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedImage, setSelectedImage] = useState(null);

  // Extract data from the nested response structure
  const data = results.data || results;
  console.log('ResultsDisplay - Full results:', results);
  console.log('ResultsDisplay - Extracted data:', data);
  
  const {
    address,
    building_insights,
    data_layers,
    roof_classification,
    gutter_estimate,
    images  // **ADDED: Extract images object from response**
  } = data;
  
  // **FIXED: Extract image data from the correct location**
  const images_analyzed = images?.images_processed || 0;
  const local_image_paths = images?.local_image_paths || [];
  const base64_images = images?.base64_images || [];
  
  console.log('ResultsDisplay - Full results:', results);
  console.log('ResultsDisplay - Extracted data:', data);
  console.log('ResultsDisplay - Roof classification:', roof_classification);
  console.log('ResultsDisplay - Images object:', images);
  console.log('ResultsDisplay - Image paths:', local_image_paths);
  console.log('ResultsDisplay - Base64 images:', base64_images);
  console.log('ResultsDisplay - Images analyzed:', images_analyzed);

  const buildingData = building_insights?.raw_api_response;
  const roofType = roof_classification?.roof_type || 'Unknown';
  const confidence = roof_classification?.confidence || 0;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'details', label: 'Building Details', icon: Info },
    { id: 'images', label: 'Satellite Images', icon: ImageIcon },
    { id: 'estimate', label: 'Gutter Estimate', icon: Ruler }
  ];

  const getConfidenceColor = (conf) => {
    if (conf >= 0.8) return 'text-success-600 bg-success-50';
    if (conf >= 0.6) return 'text-warning-600 bg-warning-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceLabel = (conf) => {
    if (conf >= 0.8) return 'High';
    if (conf >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 text-white p-6">
        <div className="flex items-center space-x-3 mb-2">
          <MapPin className="h-6 w-6" />
          <h2 className="text-2xl font-bold">{address}</h2>
        </div>
        <div className="flex items-center space-x-4 text-primary-100">
          <span className="flex items-center space-x-2">
            <Home className="h-4 w-4" />
            <span>Roof Type: {roofType}</span>
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(confidence)}`}>
            Confidence: {getConfidenceLabel(confidence)} ({(confidence * 100).toFixed(0)}%)
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Quick Stats */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Quick Summary</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Roof Type</span>
                    <span className="font-medium text-gray-900">{roofType}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">AI Confidence</span>
                    <span className={`px-2 py-1 rounded text-sm font-medium ${getConfidenceColor(confidence)}`}>
                      {(confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Images Analyzed</span>
                    <span className="font-medium text-gray-900">{images_analyzed}</span>
                  </div>
                </div>
              </div>

              {/* Gutter Estimate Summary */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Gutter Estimate</h3>
                {gutter_estimate ? (
                  <div className="bg-primary-50 p-4 rounded-lg border border-primary-200">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-primary-600 mb-2">
                        {gutter_estimate.total_gutter_ft} ft
                      </div>
                      <div className="text-sm text-primary-700">
                        Estimated Range: {gutter_estimate.estimated_range?.min || 'N/A'} - {gutter_estimate.estimated_range?.max || 'N/A'} ft
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-500">
                    No gutter estimate available
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('estimate')}
                className="flex-1 bg-primary-500 text-white py-3 px-6 rounded-lg hover:bg-primary-600 transition-colors flex items-center justify-center space-x-2"
              >
                <Ruler className="h-5 w-5" />
                <span>View Full Estimate</span>
              </button>
              <button
                onClick={() => setActiveTab('images')}
                className="flex-1 bg-gray-100 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
              >
                <ImageIcon className="h-5 w-5" />
                <span>View Satellite Images</span>
              </button>
            </div>
          </div>
        )}

        {/* Building Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Building Information</h3>
            
            {buildingData ? (
              <div className="grid md:grid-cols-2 gap-6">
                {/* Basic Info */}
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Property Details</h4>
                  <div className="space-y-3">
                    {buildingData.postalCode && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Postal Code</span>
                        <span className="font-medium">{buildingData.postalCode}</span>
                      </div>
                    )}
                    {buildingData.administrativeArea && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">State</span>
                        <span className="font-medium">{buildingData.administrativeArea}</span>
                      </div>
                    )}
                    {buildingData.imageryDate && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Imagery Date</span>
                        <span className="font-medium">
                          {buildingData.imageryDate.month}/{buildingData.imageryDate.day}/{buildingData.imageryDate.year}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Solar Potential */}
                {buildingData.solarPotential && (
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Solar Potential</h4>
                    <div className="space-y-3">
                      {buildingData.solarPotential.maxArrayPanelsCount && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Max Solar Panels</span>
                          <span className="font-medium">{buildingData.solarPotential.maxArrayPanelsCount}</span>
                        </div>
                      )}
                      {buildingData.solarPotential.maxArrayAreaMeters2 && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Max Array Area</span>
                          <span className="font-medium">{buildingData.solarPotential.maxArrayAreaMeters2.toFixed(1)} m²</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Info className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No building data available</p>
              </div>
            )}
          </div>
        )}

        {/* Images Tab */}
        {activeTab === 'images' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Satellite Imagery Analysis</h3>
            
            {base64_images && base64_images.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {base64_images.map((imageData, index) => {
                  // Skip mask images (they appear black) - only show RGB images
                  if (imageData.includes('mask')) {
                    return null; // Don't render mask images
                  }
                  
                  return (
                    <div key={index} className="group relative">
                      <img
                        src={imageData} // **FIXED: Use base64 data directly**
                        alt={`Satellite image ${index + 1}`}
                        className="w-full h-48 object-cover rounded-lg border border-gray-200 group-hover:border-primary-300 transition-colors cursor-pointer"
                        onClick={() => setSelectedImage(imageData)}
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all rounded-lg flex items-center justify-center">
                        <Eye className="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <ImageIcon className="h-12 w-8 mx-auto mb-4 text-gray-300" />
                <p>No satellite images available</p>
                <p className="text-sm text-gray-400 mt-2">
                  {images_analyzed > 0 ? `${images_analyzed} images were processed by AI` : 'Images are being processed...'}
                </p>
              </div>
            )}

            {/* Image Info */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Image Analysis</h4>
              <p className="text-sm text-gray-600">
                Our AI analyzed {images_analyzed} satellite images to determine the roof type and calculate gutter requirements.
                The images include RGB, DSM (Digital Surface Model), and mask data for comprehensive analysis.
              </p>
            </div>
          </div>
        )}

        {/* Gutter Estimate Tab */}
        {activeTab === 'estimate' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Detailed Gutter Estimate</h3>
            
            {gutter_estimate ? (
              <div className="space-y-6">
                {/* Main Estimate */}
                <div className="bg-gradient-to-r from-primary-50 to-blue-50 p-6 rounded-xl border border-primary-200">
                  <div className="text-center mb-6">
                    <div className="text-5xl font-bold text-primary-600 mb-2">
                      {gutter_estimate.total_gutter_ft} ft
                    </div>
                    <p className="text-lg text-primary-700">Total Gutter Length Required</p>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{gutter_estimate.eave_length_ft?.toFixed(1) || 'N/A'} ft</div>
                      <div className="text-sm text-gray-600">Eave Length</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{gutter_estimate.downspouts_estimate || 'N/A'}</div>
                      <div className="text-sm text-gray-600">Downspouts</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{gutter_estimate.waste_factor * 100}%</div>
                      <div className="text-sm text-gray-600">Waste Factor</div>
                    </div>
                  </div>
                </div>

                {/* Estimate Range */}
                {gutter_estimate.estimated_range && (
                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h4 className="font-medium text-gray-900 mb-3">Estimated Range</h4>
                    <div className="flex items-center justify-between">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-success-600">{gutter_estimate.estimated_range.min} ft</div>
                        <div className="text-sm text-gray-600">Minimum</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-600">{gutter_estimate.total_gutter_ft} ft</div>
                        <div className="text-sm text-gray-600">Recommended</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-warning-600">{gutter_estimate.estimated_range.max} ft</div>
                        <div className="text-sm text-gray-600">Maximum</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {gutter_estimate.warnings && gutter_estimate.warnings.length > 0 && (
                  <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                    <h4 className="font-medium text-warning-800 mb-3 flex items-center space-x-2">
                      <AlertTriangle className="h-5 w-5" />
                      <span>Important Notes</span>
                    </h4>
                    <ul className="space-y-2">
                      {gutter_estimate.warnings.map((warning, index) => (
                        <li key={index} className="text-sm text-warning-700 flex items-start space-x-2">
                          <span className="text-warning-500 mt-1">•</span>
                          <span>{warning}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Roof Type Details */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Roof Analysis</h4>
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Roof Type:</span>
                      <span className="ml-2 font-medium text-gray-900">{gutter_estimate.roof_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Confidence:</span>
                      <span className="ml-2 font-medium text-gray-900">{(gutter_estimate.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Complexity Factor:</span>
                      <span className="ml-2 font-medium text-gray-900">{gutter_estimate.complexity_factor?.toFixed(2) || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Ruler className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No gutter estimate available</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-4xl max-h-full">
            <img
              src={selectedImage} // **FIXED: Use base64 data directly**
              alt="Satellite image"
              className="max-w-full max-h-full object-contain rounded-lg"
            />
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 transition-colors"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultsDisplay;
