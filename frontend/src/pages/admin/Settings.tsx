import React from 'react';
import { Card } from '../../components/ui/Card';

export default function AdminSettings() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
      
      <Card>
        <div className="p-6">
          <p className="text-gray-500">No settings available</p>
        </div>
      </Card>
    </div>
  );
}