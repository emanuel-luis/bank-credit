import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ChevronLeft, 
  FileText, 
  Calendar, 
  Building,
  Clock, 
  AlertCircle, 
  MessageSquare, 
  Upload, 
  ArrowUpRight, 
  ExternalLink 
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../../components/ui/Card';
import ApplicationStatusBadge, { ApplicationStatus } from '../../components/loan/ApplicationStatusBadge';

// Mock data
const applicationData = {
  id: '1',
  title: 'Working Capital Loan',
  status: 'pending_documents' as ApplicationStatus,
  amount: 120000,
  department: 'Microenterprise',
  submittedAt: new Date('2025-04-10'),
  deadline: new Date('2025-05-25'),
  companyName: 'Sample Company Ltda.',
  cnpj: '12.345.678/0001-99',
  contactName: 'João Silva',
  contactEmail: 'joao@example.com',
  contactPhone: '(11) 98765-4321',
  purpose: 'Working Capital',
  term: 36,
  requiredDocuments: [
    { id: '1', name: 'Financial Statements 2024', status: 'approved' },
    { id: '2', name: 'Financial Statements 2023', status: 'approved' },
    { id: '3', name: 'Business Plan', status: 'pending' },
    { id: '4', name: 'Tax Compliance Certificate', status: 'rejected' },
  ],
  timeline: [
    { 
      id: '1', 
      date: new Date('2025-04-10T14:30:00'), 
      title: 'Application Submitted', 
      description: 'Credit application was successfully submitted.' 
    },
    { 
      id: '2', 
      date: new Date('2025-04-10T15:45:00'), 
      title: 'Document Verification', 
      description: 'Your application is undergoing initial document verification.' 
    },
    { 
      id: '3', 
      date: new Date('2025-04-11T09:15:00'), 
      title: 'Application Routed', 
      description: 'Your application has been routed to the Microenterprise department.' 
    },
    { 
      id: '4', 
      date: new Date('2025-04-15T11:30:00'), 
      title: 'Documents Requested', 
      description: 'Additional documents have been requested.' 
    },
  ],
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

export default function CustomerApplicationDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showAddDocumentModal, setShowAddDocumentModal] = useState(false);
  
  // Simulate data retrieval
  const application = applicationData;
  
  if (!application) {
    return <div>Loading...</div>;
  }
  
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<ChevronLeft className="h-4 w-4" />}
              onClick={() => navigate('/customer/applications')}
            >
              Back to Applications
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
          </div>
          <ApplicationStatusBadge status={application.status} className="text-sm px-3 py-1" />
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>{application.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Application Overview</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center text-gray-500 mb-2">
                      <Building className="h-5 w-5 mr-2" />
                      <span className="text-sm font-medium">Company Information</span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <p className="text-sm text-gray-500">Company Name</p>
                        <p className="font-medium">{application.companyName}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">CNPJ</p>
                        <p className="font-medium">{application.cnpj}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Contact</p>
                        <p className="font-medium">{application.contactName}</p>
                        <p className="text-sm">{application.contactEmail}</p>
                        <p className="text-sm">{application.contactPhone}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center text-gray-500 mb-2">
                      <FileText className="h-5 w-5 mr-2" />
                      <span className="text-sm font-medium">Loan Details</span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <p className="text-sm text-gray-500">Amount</p>
                        <p className="font-medium">{formatCurrency(application.amount)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Purpose</p>
                        <p className="font-medium">{application.purpose}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Term</p>
                        <p className="font-medium">{application.term} months</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Department</p>
                        <p className="font-medium">{application.department}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Required Documents</h3>
                {application.status === 'pending_documents' && (
                  <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <AlertCircle className="h-5 w-5 text-yellow-400" />
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-yellow-800">Action Required</h3>
                        <div className="mt-2 text-sm text-yellow-700">
                          <p>
                            Your application is missing required documents. Please upload the missing or rejected documents.
                          </p>
                        </div>
                        <div className="mt-4">
                          <Button 
                            size="sm"
                            onClick={() => setShowAddDocumentModal(true)}
                            leftIcon={<Upload className="mr-1 h-4 w-4" />}
                          >
                            Upload Documents
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {application.requiredDocuments.map((document) => (
                      <li key={document.id}>
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <FileText className="flex-shrink-0 h-5 w-5 text-gray-400" />
                              <p className="ml-2 text-sm font-medium text-gray-900">{document.name}</p>
                            </div>
                            <div>
                              {document.status === 'approved' && (
                                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                  Approved
                                </span>
                              )}
                              {document.status === 'pending' && (
                                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                  Pending Review
                                </span>
                              )}
                              {document.status === 'rejected' && (
                                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                  Rejected
                                </span>
                              )}
                            </div>
                          </div>
                          {document.status === 'rejected' && (
                            <div className="mt-2 sm:flex sm:justify-between">
                              <div className="sm:flex">
                                <p className="flex items-center text-sm text-gray-500">
                                  <AlertCircle className="flex-shrink-0 mr-1.5 h-4 w-4 text-error-400" />
                                  Document needs to be resubmitted
                                </p>
                              </div>
                              <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  onClick={() => setShowAddDocumentModal(true)}
                                >
                                  Replace
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
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
                <CardTitle>Application Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flow-root">
                  <ul className="-mb-8">
                    {application.timeline.map((event, eventIdx) => (
                      <li key={event.id}>
                        <div className="relative pb-8">
                          {eventIdx !== application.timeline.length - 1 ? (
                            <span
                              className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                              aria-hidden="true"
                            />
                          ) : null}
                          <div className="relative flex space-x-3">
                            <div>
                              <span className="h-8 w-8 rounded-full bg-primary-50 flex items-center justify-center ring-8 ring-white">
                                <Clock className="h-4 w-4 text-primary-500" />
                              </span>
                            </div>
                            <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                              <div>
                                <p className="text-sm text-gray-900">{event.title}</p>
                                <p className="mt-1 text-sm text-gray-500">{event.description}</p>
                              </div>
                              <div className="text-right text-sm whitespace-nowrap text-gray-500">
                                <time dateTime={event.date.toISOString()}>
                                  {format(event.date, 'MMM d, HH:mm', { locale: ptBR })}
                                </time>
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Status Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center">
                  <Calendar className="h-5 w-5 text-gray-400 mr-2" />
                  <div>
                    <p className="text-sm text-gray-500">Submitted</p>
                    <p className="font-medium">{format(application.submittedAt, 'PPP', { locale: ptBR })}</p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <Clock className="h-5 w-5 text-gray-400 mr-2" />
                  <div>
                    <p className="text-sm text-gray-500">Expected Completion</p>
                    <p className="font-medium">{format(application.deadline, 'PPP', { locale: ptBR })}</p>
                    <p className="text-xs text-gray-500">
                      (in {formatDistanceToNow(application.deadline, { locale: ptBR })})
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <Building className="h-5 w-5 text-gray-400 mr-2" />
                  <div>
                    <p className="text-sm text-gray-500">Current Department</p>
                    <p className="font-medium">{application.department}</p>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full"
                  leftIcon={<MessageSquare className="mr-2 h-5 w-5" />}
                  onClick={() => {}}
                >
                  Contact Loan Officer
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Need Assistance?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button 
                  variant="outline" 
                  className="w-full justify-start" 
                  rightIcon={<ExternalLink className="ml-auto h-4 w-4" />}
                  onClick={() => {}}
                >
                  <span className="flex items-center">
                    <FileText className="mr-2 h-5 w-5 text-gray-400" />
                    Application Guide
                  </span>
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start" 
                  rightIcon={<ExternalLink className="ml-auto h-4 w-4" />}
                  onClick={() => {}}
                >
                  <span className="flex items-center">
                    <FileText className="mr-2 h-5 w-5 text-gray-400" />
                    Document Requirements
                  </span>
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start" 
                  rightIcon={<ArrowUpRight className="ml-auto h-4 w-4" />}
                  onClick={() => {}}
                >
                  <span className="flex items-center">
                    <MessageSquare className="mr-2 h-5 w-5 text-gray-400" />
                    Contact Support
                  </span>
                </Button>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}