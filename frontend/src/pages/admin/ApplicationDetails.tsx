import React from 'react';
import { useParams } from 'react-router-dom';
import { ApplicationStatusBadge } from '../../components/loan/ApplicationStatusBadge';
import { Card } from '../../components/ui/Card';

export default function AdminApplicationDetails() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
        <ApplicationStatusBadge status="pending" />
      </div>

      <Card>
        <div className="p-6">
          <p className="text-gray-500">Application ID: {id}</p>
        </div>
      </Card>
    </div>
  );
}