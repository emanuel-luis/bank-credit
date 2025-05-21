import React from 'react';
import { Card } from '../../components/ui/Card';

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium">Total Applications</h3>
            <p className="text-3xl font-bold mt-2">0</p>
          </div>
        </Card>
        
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium">Active Users</h3>
            <p className="text-3xl font-bold mt-2">0</p>
          </div>
        </Card>
        
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium">Departments</h3>
            <p className="text-3xl font-bold mt-2">0</p>
          </div>
        </Card>
      </div>
    </div>
  );
}