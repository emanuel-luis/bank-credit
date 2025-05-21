import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FilePlus, ArrowRight, FileText, ChevronRight, FileCheck, AlertCircle } from 'lucide-react';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import ApplicationCard from '../../components/loan/ApplicationCard';
import { useMockApplication } from '../../context/mockdata';

export default function CustomerDashboard() {
  const navigate = useNavigate();
  const [recentApplications, setRecentApplications] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [pending, setPending] = useState(0);
  const [approved, setApproved] = useState(0);
  const { mockData } = useMockApplication();

  useEffect(() => {
    const fetchApplications = async () => {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://127.0.0.1:8000/requests/', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) return;
      const data = await response.json();
      setTotal(data.length);
      setPending(data.filter((a: any) => a.status === 'PENDING').length);
      setApproved(data.filter((a: any) => a.status === 'APPROVED').length);

      // Enriquecer com dados mockados do contexto
      const enriched = data.map((app: any) => ({
        ...app,
        ...(mockData[app.id] || {})
      }));

      // Ordena por data de atualização (updated_at) ou data de criação (created_at)
      const sorted = enriched
        .sort((a: any, b: any) => {
          const dateA = new Date(a.updated_at || a.created_at).getTime();
          const dateB = new Date(b.updated_at || b.created_at).getTime();
          return dateB - dateA;
        })
        .slice(0, 2);

      setRecentApplications(sorted);
    };
    fetchApplications();
  }, [mockData]);

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
                <h2 className="text-2xl font-bold text-gray-900">Bem-vindo ao seu painel</h2>
                <p className="mt-1 text-gray-500 max-w-2xl">
                  Inicie uma nova solicitação de crédito ou acompanhe suas solicitações existentes.
                </p>
              </div>
              <div className="mt-5 sm:mt-0">
                <Button
                  onClick={() => navigate('/customer/applications/new')}
                  rightIcon={<FilePlus className="ml-2 h-5 w-5" />}
                >
                  Nova Solicitação
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
              <CardTitle>Solicitações Recentes</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/customer/applications')}
                rightIcon={<ArrowRight className="ml-1 h-4 w-4" />}
              >
                Ver todas
              </Button>
            </CardHeader>

            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {recentApplications.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    {...application}
                    companyName={application.companyName}
                    submittedAt={application.created_at}
                    onViewDetails={(id) => navigate(`/customer/applications/${id}`)}
                  />
                ))}
                {recentApplications.length === 0 && (
                  <div className="md:col-span-2 py-10 text-center">
                    <FileText className="mx-auto h-10 w-10 text-gray-400" />
                    <h3 className="mt-2 text-sm font-semibold text-gray-900">Nenhuma solicitação</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Você ainda não enviou nenhuma solicitação de crédito.
                    </p>
                    <div className="mt-6">
                      <Button
                        variant="outline"
                        onClick={() => navigate('/customer/applications/new')}
                      >
                        Iniciar nova solicitação
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
                <CardTitle>Status das Solicitações</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-blue-100 p-2">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Total de Solicitações</p>
                        <p className="text-xl font-bold">{total}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-yellow-100 p-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Pendentes</p>
                        <p className="text-xl font-bold">{pending}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="mr-4 rounded-full bg-green-100 p-2">
                        <FileCheck className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Aprovadas</p>
                        <p className="text-xl font-bold">{approved}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Atalhos</CardTitle>
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
                      Nova Solicitação
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
                      Todas as Solicitações
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