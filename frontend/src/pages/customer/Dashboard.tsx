import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FilePlus, ArrowRight, FileText, ChevronRight, FileCheck, AlertCircle } from 'lucide-react';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import ApplicationCard from '../../components/loan/ApplicationCard';
import { ApplicationStatus } from '../../components/loan/ApplicationStatusBadge';

// Mock data
const recentApplications = [
  {
    id: '1',
    title: 'Working Capital Loan',
    status: 'under_review' as ApplicationStatus,
    amount: 120000,
    department: 'Microenterprise',
    submittedAt: new Date('2025-04-10'),
    deadline: new Date('2025-05-25'),
  },
  {
    id: '2',
    title: 'Equipment Financing',
    status: 'pending_documents' as ApplicationStatus,
    amount: 75000,
    department: 'Microenterprise',
    submittedAt: new Date('2025-04-01'),
    deadline: new Date('2025-05-16'),
    hasSlaWarning: true,
  },
];

export default function CustomerDashboard() {
  const navigate = useNavigate();
  
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="text-center sm:text-left sm:flex sm:items-center sm:justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Welcome to your dashboard</h2>
                <p className="mt-1 text-gray-500 max-w-2xl">
                  Start a new credit application or track your existing applications.
                </p>
              </div>
              <div className="mt-5 sm:mt-0">
                <Button
                  onClick={() => navigate('/customer/applications/new')}
                  rightIcon={<FilePlus className="ml-2 h-5 w-5" />}
                >
                  New Application
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recent Applications</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/customer/applications')}
                rightIcon={<ArrowRight className="ml-1 h-4 w-4" />}
              >
                View all
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {recentApplications.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    {...application}
                    onViewDetails={(id) => navigate(`/customer/applications/${id}`)}
                  />
                ))}
                {recentApplications.length === 0 && (
                  <div className="md:col-span-2 py-10 text-center">
                    <FileText className="mx-auto h-10 w-10 text-gray-400" />
                    <h3 className="mt-2 text-sm font-semibold text-gray-900">No applications</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      You haven't submitted any credit applications yet.
                    </p>
                    <div className="mt-6">
                      <Button
                        variant="outline"
                        onClick={() => navigate('/customer/applications/new')}
                      >
                        Start a new application
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Application Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-blue-100 p-2">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Total Applications</p>
                        <p className="text-xl font-bold">2</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-yellow-100 p-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Pending</p>
                        <p className="text-xl font-bold">2</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-green-100 p-2">
                        <FileCheck className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Approved</p>
                        <p className="text-xl font-bold">0</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Links</CardTitle>
              </CardHeader>
              <CardContent>
                <nav className="space-y-1">
                  <Button 
                    variant="ghost" 
                    className="w-full justify-between" 
                    onClick={() => navigate('/customer/applications/new')}
                  >
                    <span className="flex items-center">
                      <FilePlus className="mr-3 h-5 w-5 text-gray-400" />
                      New Application
                    </span>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    className="w-full justify-between" 
                    onClick={() => navigate('/customer/applications')}
                  >
                    <span className="flex items-center">
                      <FileText className="mr-3 h-5 w-5 text-gray-400" />
                      All Applications
                    </span>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </Button>
                </nav>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}