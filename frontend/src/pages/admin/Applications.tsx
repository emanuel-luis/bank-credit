import React from 'react';
import { ApplicationCard } from '../../components/loan/ApplicationCard';

export default function AdminApplications() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">All Applications</h1>
      
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow">
          <div className="p-4">
            <p className="text-gray-500">No applications found</p>
          </div>
        </div>
      </div>
    </div>
  );
}