import React from 'react';
import { Card } from '../../components/ui/Card';
import ApplicationCard from '../../components/loan/ApplicationCard';

export default function Applications() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Loan Applications</h1>
      </div>

      <Card className="overflow-hidden">
        <div className="p-6">
          <div className="space-y-4">
            {/* Applications will be mapped here */}
            <ApplicationCard
              id="placeholder"
              title="Loading..."
              status="pending"
              amount={0}
              department="Loading..."
              submittedAt={new Date()}
              onViewDetails={() => {}}
            />
          </div>
        </div>
      </Card>
    </div>
  );
}