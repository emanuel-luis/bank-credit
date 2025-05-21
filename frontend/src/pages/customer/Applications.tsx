import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FilePlus, Filter, Search, FileText } from 'lucide-react';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { useMockApplication } from '../../context/mockdata';

// Função utilitária para formatar datas
function formatDate(dateStr?: string) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// Função utilitária para formatar status
function formatStatus(status?: string) {
  switch (status) {
    case 'PENDING':
      return <span className="inline-block px-2 py-1 rounded bg-yellow-100 text-yellow-800 text-xs font-semibold">Pendente</span>;
    case 'APPROVED':
      return <span className="inline-block px-2 py-1 rounded bg-green-100 text-green-800 text-xs font-semibold">Aprovado</span>;
    case 'REJECTED':
      return <span className="inline-block px-2 py-1 rounded bg-red-100 text-red-800 text-xs font-semibold">Rejeitado</span>;
    case 'under_review':
      return <span className="inline-block px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs font-semibold">Em análise</span>;
    case 'document_check':
      return <span className="inline-block px-2 py-1 rounded bg-purple-100 text-purple-800 text-xs font-semibold">Checagem de documentos</span>;
    default:
      return <span className="inline-block px-2 py-1 rounded bg-gray-100 text-gray-800 text-xs font-semibold">{status || '-'}</span>;
  }
}

export default function CustomerApplications() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { mockData } = useMockApplication();

  useEffect(() => {
    const fetchApplications = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('http://127.0.0.1:8000/requests/', {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) throw new Error('Erro ao buscar solicitações');
        const data = await response.json();

        // Enriquecer com dados mockados do contexto
        const enriched = data.map((app: any) => ({
          ...app,
          ...(mockData[app.id] || {})
        }));

        setApplications(enriched);
      } catch (e) {
        setApplications([]);
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, [mockData]);

  const filteredApplications = applications.filter(app => {
    const matchesSearch = app.id.toString().includes(searchTerm);
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
                <h2 className="text-xl font-bold text-gray-900">Minhas Solicitações</h2>
                <p className="mt-1 text-sm text-gray-500">
                  Veja e gerencie todas as suas solicitações de crédito.
                </p>
              </div>
              <div className="mt-4 sm:mt-0">
                <Button
                  onClick={() => navigate('/customer/applications/new')}
                  leftIcon={<FilePlus className="mr-2 h-5 w-5" />}
                >
                  Nova Solicitação
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
              <CardTitle>Solicitações</CardTitle>
              <div className="flex space-x-2">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Buscar por ID..."
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
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="all">Todos os status</option>
                    <option value="PENDING">Pendente</option>
                    <option value="APPROVED">Aprovado</option>
                    <option value="REJECTED">Rejeitado</option>
                  </select>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-12 text-center">Carregando...</div>
            ) : filteredApplications.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredApplications.map((app) => (
                  <Card
                    key={app.id}
                    className="flex flex-col justify-between shadow-lg border border-gray-200 hover:border-primary-400 transition"
                  >
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base font-semibold text-primary-700 flex flex-col">
                        Solicitação #{app.id}
                        <span className="text-sm font-normal text-gray-600 mt-1">
                          {app.companyName || '-'}
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col gap-2">
                      <div>
                        <span className="font-medium">Status: </span>
                        {formatStatus(app.status)}
                      </div>
                      <div>
                        <span className="font-medium">Valor: </span>
                        {app.amount ? `R$ ${Number(app.amount).toLocaleString('pt-BR')}` : '-'}
                      </div>
                      <div>
                        <span className="font-medium">Criado em: </span>
                        {formatDate(app.created_at)}
                      </div>
                      <div>
                        <span className="font-medium">CNPJ: </span>
                        {app.cnpj || '-'}
                      </div>
                      <div>
                        <span className="font-medium">Central: </span>
                        {app.central || '-'}
                      </div>
                    </CardContent>
                    <div className="p-4 pt-0">
                      <Button
                        className="w-full"
                        onClick={() => navigate(`/customer/applications/${app.id}`)}
                      >
                        Ver detalhes
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma solicitação encontrada</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Nenhuma solicitação corresponde aos filtros atuais.
                </p>
                {(statusFilter !== 'all' || searchTerm !== '') && (
                  <div className="mt-6 flex justify-center">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setStatusFilter('all');
                        setSearchTerm('');
                      }}
                    >
                      Limpar filtros
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