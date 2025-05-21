import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  FileText, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  BarChart,
  ArrowUpRight,
  ArrowDownRight,
  Users
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useAuth } from '../../contexts/AuthContext';
import ApplicationStatusBadge, { ApplicationStatus } from '../../components/loan/ApplicationStatusBadge';

// Mock data
const pendingApplications = [
  {
    id: '1',
    companyName: 'Tech Solutions Ltda.',
    title: 'Working Capital Loan',
    amount: 120000,
    status: 'under_review' as ApplicationStatus,
    submittedAt: new Date('2025-04-10'),
    daysRemaining: 15
  },
  {
    id: '2',
    companyName: 'Green Energy Brazil',
    title: 'Equipment Financing',
    amount: 85000,
    status: 'document_check' as ApplicationStatus,
    submittedAt: new Date('2025-04-12'),
    daysRemaining: 18
  },
  {
    id: '3',
    companyName: 'Organic Farms Nordeste',
    title: 'Expansion Loan',
    amount: 95000,
    status: 'document_check' as ApplicationStatus,
    submittedAt: new Date('2025-04-08'),
    daysRemaining: 7,
    isUrgent: true
  }
];

const slaWarnings = [
  {
    id: '3',
    companyName: 'Organic Farms Nordeste',
    title: 'Expansion Loan',
    days: 7,
    threshold: 10
  },
  {
    id: '4',
    companyName: 'Recife Textiles',
    title: 'Inventory Financing',
    days: 5,
    threshold: 10
  }
];

export default function StaffDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(timer);
    };
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

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
                <p className="text-sm text-gray-500">
                  {currentTime.toLocaleDateString('pt-BR', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </p>
                <h2 className="text-2xl font-bold text-gray-900">Good day, {user?.name.split(' ')[0]}</h2>
                <p className="mt-1 text-gray-500 max-w-2xl">
                  You have <span className="font-medium text-primary-600">{pendingApplications.length}</span> pending applications and{' '}
                  <span className="font-medium text-warning-600">{slaWarnings.length}</span> SLA warnings.
                </p>
              </div>
              <div className="mt-5 sm:mt-0">
                <Button
                  onClick={() => navigate('/staff/applications')}
                >
                  View All Applications
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="rounded-full bg-green-100 p-3">
                  <FileText className="h-8 w-8 text-green-600" />
                </div>
                <div className="bg-green-50 rounded-full px-3 py-1 flex items-center">
                  <ArrowUpRight className="h-4 w-4 text-green-600 mr-1" />
                  <span className="text-xs font-medium text-green-600">12%</span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Total Applications</h3>
                <p className="text-3xl font-bold text-gray-900">24</p>
                <div className="mt-1 text-sm text-gray-500">For current month</div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="rounded-full bg-blue-100 p-3">
                  <Clock className="h-8 w-8 text-blue-600" />
                </div>
                <div className="bg-red-50 rounded-full px-3 py-1 flex items-center">
                  <ArrowDownRight className="h-4 w-4 text-red-600 mr-1" />
                  <span className="text-xs font-medium text-red-600">8%</span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Pending Review</h3>
                <p className="text-3xl font-bold text-gray-900">7</p>
                <div className="mt-1 text-sm text-gray-500">Awaiting action</div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="rounded-full bg-yellow-100 p-3">
                  <AlertTriangle className="h-8 w-8 text-yellow-600" />
                </div>
                <div className="bg-red-50 rounded-full px-3 py-1 flex items-center">
                  <ArrowUpRight className="h-4 w-4 text-red-600 mr-1" />
                  <span className="text-xs font-medium text-red-600">15%</span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">SLA Warnings</h3>
                <p className="text-3xl font-bold text-gray-900">{slaWarnings.length}</p>
                <div className="mt-1 text-sm text-gray-500">Approaching deadline</div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="rounded-full bg-green-100 p-3">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div className="bg-green-50 rounded-full px-3 py-1 flex items-center">
                  <ArrowUpRight className="h-4 w-4 text-green-600 mr-1" />
                  <span className="text-xs font-medium text-green-600">20%</span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Completed</h3>
                <p className="text-3xl font-bold text-gray-900">12</p>
                <div className="mt-1 text-sm text-gray-500">This month</div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pending Applications</CardTitle>
                  <CardDescription>
                    Applications that require your attention
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => navigate('/staff/applications')}
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full whitespace-nowrap">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Company
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Application
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Days Left
                      </th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pendingApplications.map((application) => (
                      <tr key={application.id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{application.companyName}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{application.title}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{formatCurrency(application.amount)}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <ApplicationStatusBadge status={application.status} />
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${
                            application.daysRemaining <= 7 ? 'text-error-600' : 'text-gray-900'
                          }`}>
                            {application.daysRemaining} days
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => navigate(`/staff/applications/${application.id}`)}
                          >
                            Review
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <div className="grid grid-cols-1 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>SLA Warnings</CardTitle>
                    <CardDescription>
                      Applications approaching deadline
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {slaWarnings.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {slaWarnings.map((warning) => (
                      <li key={warning.id} className="py-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{warning.companyName}</p>
                            <p className="text-sm text-gray-500">{warning.title}</p>
                          </div>
                          <div className="flex items-center">
                            <div className="flex items-center mr-4">
                              <AlertTriangle className="h-4 w-4 text-warning-500 mr-1" />
                              <span className="text-sm font-medium text-warning-600">
                                {warning.days} days left
                              </span>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/staff/applications/${warning.id}`)}
                            >
                              View
                            </Button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-6">
                    <CheckCircle className="mx-auto h-10 w-10 text-success-500" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No SLA warnings</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      All applications are within normal processing times.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Monthly Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[200px] flex items-center justify-center">
                  <div className="flex flex-col items-center">
                    <BarChart3 className="h-16 w-16 text-gray-300" />
                    <p className="mt-2 text-sm text-gray-500">Performance charts will display here</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}