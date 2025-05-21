import React from 'react';

const ManagerDashboard = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Manager Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Dashboard content will go here */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Overview</h2>
          <p className="text-gray-600">Welcome to the manager dashboard</p>
        </div>
      </div>
    </div>
  );
};

export default ManagerDashboard;