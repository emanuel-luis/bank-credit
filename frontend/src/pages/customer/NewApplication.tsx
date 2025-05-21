import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Upload, X, FileText, CheckCircle, AlertCircle, ChevronLeft } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../../components/ui/Card';
import { useAuth } from '../../contexts/AuthContext';
import { useMockApplication } from '../../context/mockdata';

type ApplicationFormData = {
  companyName: string;
  cnpj: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  amount: number;
  purpose: string;
  term: number;
  documents: File[];
};

export default function CustomerNewApplication() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [success, setSuccess] = useState(false);

  // Use o contexto para mockar os dados em memória
  const { setMockData } = useMockApplication();
  const { register, handleSubmit, formState: { errors }, trigger, getValues } = useForm<ApplicationFormData>();

  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    onDrop: (acceptedFiles) => {
      setUploadedFiles(prev => [...prev, ...acceptedFiles]);
    },
  });

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  function formatDateNoZ(date: Date) {
    return date.toISOString().replace(/Z$/, '');
  }

  function splitFormData(values: ApplicationFormData) {
    // Dados que vão para a API
    const apiData = {
      amount: values.amount,
      deliver_date: formatDateNoZ(new Date()),
      checklist: []
    };
    // Dados mockados (não enviados para a API)
    const mockData = {
      companyName: values.companyName,
      cnpj: values.cnpj,
      contactName: values.contactName,
      contactEmail: values.contactEmail,
      contactPhone: values.contactPhone,
      purpose: values.purpose,
      term: values.term,
      documents: values.documents || [],
    };
    return { apiData, mockData };
  }

    const onSubmit = async () => {
    setIsSubmitting(true);
    try {
      const values = getValues();
      const { apiData, mockData } = splitFormData(values);

      // Adiciona os arquivos enviados ao mockData, se houver
      if (uploadedFiles.length > 0) {
        mockData.documents = uploadedFiles.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type,
        }));
      }

      const token = localStorage.getItem('access_token');

      const response = await fetch('http://127.0.0.1:8000/requests/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify(apiData)
      });

      if (!response.ok) {
        throw new Error('Erro ao enviar solicitação');
      }

      // Recupera o id da nova solicitação criada
      const responseData = await response.json();
      const newId = responseData.id;

      // Salva os dados mockados no contexto (em memória)
      setMockData(newId, mockData);

      setSuccess(true);
      setTimeout(() => {
        navigate('/customer/applications');
      }, 2000);
    } catch (err) {
      alert('Erro ao enviar solicitação');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Validação para impedir avanço sem preencher campos obrigatórios
  const handleNextStep = async () => {
    let valid = false;
    if (currentStep === 1) {
      valid = await trigger(['companyName', 'cnpj', 'contactName', 'contactEmail', 'contactPhone']);
    } else if (currentStep === 2) {
      valid = await trigger(['amount', 'purpose', 'term']);
    } else if (currentStep === 3) {
      valid = uploadedFiles.length > 0;
      if (!valid) {
        alert('Por favor, envie pelo menos um documento.');
      }
    } else {
      valid = true;
    }
    if (valid) {
      setCurrentStep(prev => prev + 1);
      window.scrollTo(0, 0);
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => prev - 1);
    window.scrollTo(0, 0);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <>
            <CardHeader>
              <CardTitle>Informações da Empresa</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Nome da Empresa
                  </label>
                  <input
                    type="text"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.companyName ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Digite o nome da empresa"
                    {...register('companyName', { required: 'Company name is required' })}
                  />
                  {errors.companyName && (
                    <p className="mt-1 text-sm text-red-600">{errors.companyName.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    CNPJ
                  </label>
                  <input
                    type="text"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.cnpj ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="XX.XXX.XXX/XXXX-XX"
                    {...register('cnpj', {
                      required: 'CNPJ is required',
                      pattern: {
                        value: /^\d{2}\.\d{3}\.\d{3}\/\d{4}\-\d{2}$/,
                        message: 'Please enter a valid CNPJ'
                      }
                    })}
                  />
                  {errors.cnpj && (
                    <p className="mt-1 text-sm text-red-600">{errors.cnpj.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Nome
                  </label>
                  <input
                    type="text"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.contactName ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter contact name"
                    {...register('contactName', { required: 'Contact name is required' })}
                  />
                  {errors.contactName && (
                    <p className="mt-1 text-sm text-red-600">{errors.contactName.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.contactEmail ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter contact email"
                    {...register('contactEmail', {
                      required: 'Contact email is required',
                      pattern: {
                        value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: 'Please enter a valid email address'
                      }
                    })}
                  />
                  {errors.contactEmail && (
                    <p className="mt-1 text-sm text-red-600">{errors.contactEmail.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Telefone
                  </label>
                  <input
                    type="tel"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.contactPhone ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="(XX) XXXXX-XXXX"
                    {...register('contactPhone', { required: 'Contact phone is required' })}
                  />
                  {errors.contactPhone && (
                    <p className="mt-1 text-sm text-red-600">{errors.contactPhone.message}</p>
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button onClick={handleNextStep}>
                Continue
              </Button>
            </CardFooter>
          </>
        );
      case 2:
        return (
          <>
            <CardHeader>
              <CardTitle>Loan Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Loan Amount (BRL)
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <span className="text-gray-500 sm:text-sm">R$</span>
                    </div>
                    <input
                      type="number"
                      className={`pl-10 mt-1 block w-full rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                        errors.amount ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="0.00"
                      step="1000"
                      min={10000}
                      {...register('amount', {
                        required: 'Loan amount is required',
                        min: {
                          value: 10000,
                          message: 'Minimum loan amount is R$ 10,000'
                        }
                      })}
                    />
                  </div>
                  {errors.amount && (
                    <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Loan Purpose
                  </label>
                  <select
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.purpose ? 'border-red-300' : 'border-gray-300'
                    }`}
                    {...register('purpose', { required: 'Loan purpose is required' })}
                  >
                    <option value="">Select a purpose</option>
                    <option value="working_capital">Working Capital</option>
                    <option value="expansion">Business Expansion</option>
                    <option value="equipment">Equipment Financing</option>
                    <option value="refinancing">Debt Refinancing</option>
                    <option value="inventory">Inventory Purchase</option>
                    <option value="other">Other</option>
                  </select>
                  {errors.purpose && (
                    <p className="mt-1 text-sm text-red-600">{errors.purpose.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Loan Term (months)
                  </label>
                  <input
                    type="number"
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${
                      errors.term ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter loan term in months"
                    min={6}
                    max={120}
                    {...register('term', {
                      required: 'Loan term is required',
                      min: {
                        value: 6,
                        message: 'Minimum term is 6 months'
                      },
                      max: {
                        value: 120,
                        message: 'Maximum term is 120 months'
                      }
                    })}
                  />
                  {errors.term && (
                    <p className="mt-1 text-sm text-red-600">{errors.term.message}</p>
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNextStep}>
                Continue
              </Button>
            </CardFooter>
          </>
        );
      case 3:
        return (
          <>
            <CardHeader>
              <CardTitle>Document Upload</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <p className="text-sm text-gray-500">
                    Please upload the following required documents:
                  </p>
                  <ul className="mt-2 list-disc pl-5 text-sm text-gray-700 space-y-1">
                    <li>Company Registration (CNPJ)</li>
                    <li>Financial Statements (last 2 years)</li>
                    <li>Business Plan</li>
                    <li>Tax Compliance Certificates</li>
                    <li>Collateral Documentation (if applicable)</li>
                  </ul>
                </div>
                <div
                  {...getRootProps()}
                  className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:bg-gray-50"
                >
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                      >
                        <span>Upload files</span>
                        <input {...getInputProps()} />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PDF, DOC, DOCX, XLS, XLSX up to 10MB each</p>
                  </div>
                </div>
                {uploadedFiles.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Uploaded Documents</h4>
                    <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                      {uploadedFiles.map((file, index) => (
                        <li key={index} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                          <div className="flex items-center">
                            <FileText className="flex-shrink-0 h-5 w-5 text-gray-400 mr-2" />
                            <span className="ml-2 flex-1 truncate">{file.name}</span>
                          </div>
                          <div className="ml-4 flex-shrink-0">
                            <button
                              type="button"
                              className="font-medium text-error-600 hover:text-error-500"
                              onClick={() => removeFile(index)}
                            >
                              <X className="h-5 w-5" />
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {uploadedFiles.length === 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <AlertCircle className="h-5 w-5 text-yellow-400" />
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-yellow-800">Attention needed</h3>
                        <div className="mt-2 text-sm text-yellow-700">
                          <p>
                            You haven't uploaded any documents yet. Document upload is required for your application to be processed.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNextStep}>
                Continue
              </Button>
            </CardFooter>
          </>
        );
      case 4:
      default:
        const values = getValues();
        return (
          <>
            <CardHeader>
              <CardTitle>Review & Submit</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Informações da Empresa</h3>
                  <div className="mt-2 border-t border-gray-200 pt-4">
                    <dl className="divide-y divide-gray-200">
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Nome da Empresa</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.companyName}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">CNPJ</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.cnpj}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Nome</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.contactName}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Email</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.contactEmail}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Telefone</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.contactPhone}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Loan Information</h3>
                  <div className="mt-2 border-t border-gray-200 pt-4">
                    <dl className="divide-y divide-gray-200">
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Loan Amount</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">R$ {values.amount?.toLocaleString('pt-BR')}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Loan Purpose</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.purpose}</dd>
                      </div>
                      <div className="py-2 sm:grid sm:grid-cols-3 sm:gap-4">
                        <dt className="text-sm font-medium text-gray-500">Loan Term</dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{values.term} months</dd>
                      </div>
                    </dl>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Documents</h3>
                  <div className="mt-2 border-t border-gray-200 pt-4">
                    {uploadedFiles.length > 0 ? (
                      <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                        {uploadedFiles.map((file, index) => (
                          <li key={index} className="pl-3 pr-4 py-3 flex items-center text-sm">
                            <CheckCircle className="flex-shrink-0 h-5 w-5 text-success-500 mr-2" />
                            <span className="truncate">{file.name}</span>
                            <span className="ml-2 text-gray-500">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm text-gray-500 italic">No documents uploaded</div>
                    )}
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <CheckCircle className="h-5 w-5 text-success-500" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-gray-700">
                        By submitting this application, you confirm that all the information provided is accurate and complete.
                        Your application will be reviewed in accordance with Banco do Nordeste's credit policies.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={prevStep}>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button
                onClick={handleSubmit(onSubmit)}
                isLoading={isSubmitting}
              >
                Submit Application
              </Button>
            </CardFooter>
          </>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">New Credit Application</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/customer/applications')}
        >
          Cancel
        </Button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden px-4 py-8">
        <div className="px-4 py-5">
          <nav aria-label="Progress">
            <ol className="flex items-center gap-x-8">
              {['Informações', 'Detalhes Empréstimo', 'Documentos', 'Análise e Envio'].map((step, index) => {
                const isCompleted = currentStep > index + 1;
                const isCurrent = currentStep === index + 1;

                return (
                  <li key={step} className="relative pr-8 sm:pr-20">
                    {isCompleted ? (
                      <div className="absolute inset-0 flex items-center" aria-hidden="true">
                        <div className="h-0.5 w-full bg-primary-600"></div>
                      </div>
                    ) : (
                      <div className="absolute inset-0 flex items-center" aria-hidden="true">
                        <div className="h-0.5 w-full bg-gray-200"></div>
                      </div>
                    )}
                    <div
                      className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
                        isCompleted
                          ? 'bg-primary-600 group'
                          : isCurrent
                          ? 'bg-white border-2 border-primary-600'
                          : 'bg-white border-2 border-gray-300'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="h-5 w-5 text-white" aria-hidden="true" />
                      ) : (
                        <span
                          className={`${
                            isCurrent ? 'text-primary-600' : 'text-gray-500'
                          } text-sm font-medium`}
                        >
                          {index + 1}
                        </span>
                      )}
                    </div>
                    <div className="hidden sm:block absolute top-12 left-1/2 transform -translate-x-1/2 whitespace-nowrap mt-2">
                      <span
                        className={`text-sm font-medium ${
                          isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-500'
                        }`}
                      >
                        {step}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>
      </div>

      <Card>
        {renderStep()}
      </Card>

      {/* Modal simples de sucesso */}
      {success && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg p-8 flex flex-col items-center">
            <CheckCircle className="h-12 w-12 text-green-500 mb-2" />
            <div className="text-lg font-bold mb-2">Solicitação enviada!</div>
            <div className="text-gray-600 mb-4 text-center">
              Sua solicitação de crédito foi enviada com sucesso.<br />
              Você será redirecionado para suas solicitações.
            </div>
            <Button onClick={() => navigate('/customer/applications')}>OK</Button>
          </div>
        </div>
      )}
    </motion.div>
  );
}