import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FilePlus, Filter, Search, FileText } from 'lucide-react';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import ApplicationCard from '../../components/loan/ApplicationCard';
import { ApplicationStatus } from '../../components/loan/ApplicationStatusBadge';

// Mock data
const allApplications = [
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
  {
    id: '3',
    title: 'Business Expansion',
    status: 'draft' as ApplicationStatus,
    amount: 250000,
    department: 'Large Business',
    submittedAt: new Date('2025-03-15'),
  },
];

export default function CustomerApplications() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | 'all'>('all');
  
  const filteredApplications = allApplications.filter(app => {
    const matchesSearch = app.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="sm:flex sm:items-center sm:justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900">My Applications</h2>
                <p className="mt-1 text-sm text-gray-500">
                  View and manage all your credit applications.
                </p>
              </div>
              <div className="mt-4 sm:mt-0">
                <Button
                  onClick={() => navigate('/customer/applications/new')}
                  leftIcon={<FilePlus className="mr-2 h-5 w-5" />}
                >
                  New Application
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-2 sm:space-y-0">
              <CardTitle>Applications</CardTitle>
              <div className="flex space-x-2">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Search applications..."
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Filter className="h-4 w-4 text-gray-400" />
                  </div>
                  <select
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as ApplicationStatus | 'all')}
                  >
                    <option value="all">All statuses</option>
                    <option value="draft">Draft</option>
                    <option value="submitted">Submitted</option>
                    <option value="document_check">Document Check</option>
                    <option value="under_review">Under Review</option>
                    <option value="pending_documents">Pending Documents</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="escalated">Escalated</option>
                  </select>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {filteredApplications.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredApplications.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    {...application}
                    onViewDetails={(id) => navigate(`/customer/applications/${id}`)}
                  />
                ))}
              </div>
            ) : (
              <div className="py-12 text-center">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No applications found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  No applications match your current filters.
                </p>
                {statusFilter !== 'all' || searchTerm !== '' ? (
                  <div className="mt-6 flex justify-center">
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setStatusFilter('all');
                        setSearchTerm('');
                      }}
                    >
                      Clear filters
                    </Button>
                  </div>
                ) : (
                  <div className="mt-6 flex justify-center">
                    <Button onClick={() => navigate('/customer/applications/new')}>
                      Create new application
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}