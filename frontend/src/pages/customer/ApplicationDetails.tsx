import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ChevronLeft,
  FileText,
  Calendar,
  Building,
  Clock,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import ApplicationStatusBadge from '../../components/loan/ApplicationStatusBadge';
import { useMockApplication } from '../../context/mockdata';

// Função para formatar moeda
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

export default function CustomerApplicationDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [application, setApplication] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<any>(null);
  const validStatuses = ['PENDING', 'APPROVED', 'REJECTED'];
  const { getMockData } = useMockApplication();

  useEffect(() => {
    const fetchApplication = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        // Busca os dados da solicitação pelo ID
        const response = await fetch(`http://127.0.0.1:8000/requests/${id}/`, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) throw new Error('Erro ao buscar dados');
        const data = await response.json();
        setApplication(data);

        // Busca os dados mockados do contexto
        const mock = getMockData(Number(id));
        setFormData(mock || null);
      } catch (e) {
        setApplication(null);
        setFormData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchApplication();
  }, [id, getMockData]);

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!application) {
    return <div>Não foi possível carregar os dados da solicitação.</div>;
  }

  const safeStatus = validStatuses.includes(application.status) ? application.status : 'PENDING';

  // Usa os dados da API, e se não vier, usa do formulário mockado salvo no contexto
  const companyName = application.company_name || formData?.companyName || '-';
  const cnpj = application.cnpj || formData?.cnpj || '-';
  const contactName = application.contact_name || formData?.contactName || '-';
  const contactEmail = application.contact_email || formData?.contactEmail || '-';
  const contactPhone = application.contact_phone || formData?.contactPhone || '-';
  const purpose = application.purpose || formData?.purpose || '-';
  const term = application.term || formData?.term || '-';
  const department = formData?.departamento || formData?.stage || application.department || '-';

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<ChevronLeft className="h-4 w-4" />}
              onClick={() => navigate('/customer/applications')}
            >
              Voltar para Solicitações
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">Detalhes da Solicitação</h1>
          </div>
          <ApplicationStatusBadge status={safeStatus} className="text-sm px-3 py-1" />
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
              <CardTitle>
                Solicitação #{application.id}
                <span className="block text-sm font-normal text-gray-500 mt-1">
                  {companyName}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center text-gray-500 mb-3">
                    <Building className="h-5 w-5 mr-2" />
                    <span className="text-base font-medium">Empresa</span>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-500">Nome</span>
                      <div className="font-semibold">{companyName}</div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">CNPJ</span>
                      <div className="font-semibold">{cnpj}</div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Contato</span>
                      <div className="font-semibold">{contactName}</div>
                      <div className="text-sm">{contactEmail}</div>
                      <div className="text-sm">{contactPhone}</div>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center text-gray-500 mb-3">
                    <FileText className="h-5 w-5 mr-2" />
                    <span className="text-base font-medium">Empréstimo</span>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-500">Valor</span>
                      <div className="font-semibold">{formatCurrency(application.amount)}</div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Finalidade</span>
                      <div className="font-semibold">{purpose}</div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Prazo</span>
                      <div className="font-semibold">{term !== '-' ? `${term} meses` : '-'}</div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Departamento</span>
                      <div className="font-semibold">{department}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Documentos / Checklist</h3>
                <div className="bg-white shadow rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {/* Mostra documentos enviados do mockData se existirem */}
                    {formData?.documents && formData.documents.length > 0 ? (
                      formData.documents.map((doc: any, idx: number) => (
                        <li key={idx}>
                          <div className="px-4 py-4 sm:px-6 flex items-center justify-between">
                            <div className="flex items-center">
                              <FileText className="flex-shrink-0 h-5 w-5 text-gray-400" />
                              <span className="ml-2 text-sm font-medium text-gray-900">{doc.name}</span>
                            </div>
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                              Enviado
                            </span>
                          </div>
                        </li>
                      ))
                    ) : (
                      // Se não houver documentos mockados, mostra checklist da API ou mensagem padrão
                      (application.checklist && application.checklist.length > 0) ? (
                        application.checklist.map((doc: any, idx: number) => (
                          <li key={idx}>
                            <div className="px-4 py-4 sm:px-6 flex items-center justify-between">
                              <div className="flex items-center">
                                <FileText className="flex-shrink-0 h-5 w-5 text-gray-400" />
                                <span className="ml-2 text-sm font-medium text-gray-900">{doc.name || 'Documento'}</span>
                              </div>
                              <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                {doc.status || 'Pendente'}
                              </span>
                            </div>
                          </li>
                        ))
                      ) : (
                        <li>
                          <div className="px-4 py-4 text-gray-500 text-sm">Nenhum documento enviado.</div>
                        </li>
                      )
                    )}
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
                <CardTitle>Status e Informações</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col gap-4">
                  <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-4 shadow-sm">
                    <Calendar className="h-6 w-6 text-blue-500" />
                    <div>
                      <span className="text-xs text-gray-500">Criado em</span>
                      <div className="font-semibold text-gray-900">
                        {application.created_at
                          ? format(parseISO(application.created_at), 'PPP', { locale: ptBR })
                          : '-'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-4 shadow-sm">
                    <Clock className="h-6 w-6 text-green-500" />
                    <div>
                      <span className="text-xs text-gray-500">Parcelas</span>
                      <div className="font-semibold text-gray-900">
                        {term !== '-' ? `${term} meses` : '-'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-4 shadow-sm">
                    <Building className="h-6 w-6 text-purple-500" />
                    <div>
                      <span className="text-xs text-gray-500">Departamento Atual</span>
                      <div className="font-semibold text-gray-900">{department}</div>
                    </div>
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