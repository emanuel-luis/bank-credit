import React from 'react';

const ManagerApplications = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Applications</h1>
      <div className="bg-white rounded-lg shadow">
        {/* Applications list will go here */}
        <div className="p-6">
          <p className="text-gray-600">No applications to display</p>
        </div>
      </div>
    </div>
  );
};

export default ManagerApplications;