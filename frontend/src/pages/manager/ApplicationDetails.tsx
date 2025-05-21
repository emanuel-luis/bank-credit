import React from 'react';
import { useParams } from 'react-router-dom';

const ManagerApplicationDetails = () => {
  const { id } = useParams();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Application Details</h1>
      <div className="bg-white rounded-lg shadow p-6">
        {/* Application details will go here */}
        <p className="text-gray-600">Loading application {id}...</p>
      </div>
    </div>
  );
};

export default ManagerApplicationDetails;