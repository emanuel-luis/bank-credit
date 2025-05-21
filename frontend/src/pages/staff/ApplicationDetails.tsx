import React from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { ApplicationStatusBadge } from '../../components/loan/ApplicationStatusBadge';

export default function ApplicationDetails() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Application Details</h1>
        <ApplicationStatusBadge status="pending" />
      </div>

      <Card>
        <div className="p-6">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Application #{id}</h2>
              <p className="mt-1 text-sm text-gray-500">View and process application details</p>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Applicant Name</dt>
                  <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Application Date</dt>
                  <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Loan Amount</dt>
                  <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Loan Term</dt>
                  <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}