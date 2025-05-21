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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { useAuth } from '../../contexts/AuthContext';
import ApplicationStatusBadge from '../../components/loan/ApplicationStatusBadge';
import { useMockApplication } from '../../context/mockdata';

// Gráfico
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
// Importação correta do plugin
import ChartDataLabels from 'chartjs-plugin-datalabels';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ChartDataLabels);

export default function StaffDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [applications, setApplications] = useState<any[]>([]);
  const [pending, setPending] = useState<any[]>([]);
  const [approved, setApproved] = useState<any[]>([]);
  const [rejected, setRejected] = useState<any[]>([]);
  const [underReview, setUnderReview] = useState<any[]>([]);
  const [slaWarnings, setSlaWarnings] = useState<any[]>([]);
  const { mockData } = useMockApplication();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const fetchApplications = async () => {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://127.0.0.1:8000/requests/all', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) return;
      const data = await response.json();

      // Enriquecer com dados do mockData (contexto)
      const enriched = data.map((app: any) => ({
        ...app,
        ...(mockData[app.id] || {})
      }));

      setApplications(enriched);
      setPending(enriched.filter((a: any) => a.status === 'PENDING'));
      setApproved(enriched.filter((a: any) => a.status === 'APPROVED'));
      setRejected(enriched.filter((a: any) => a.status === 'REJECTED'));
      setUnderReview(enriched.filter((a: any) => a.status === 'under_review' || a.status === 'document_check'));

      // SLA warnings: exemplo, prazo de entrega em até 7 dias
      setSlaWarnings(
        enriched.filter((a: any) => {
          if (!a.deliver_date) return false;
          const daysLeft = Math.ceil((new Date(a.deliver_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
          return daysLeft <= 7 && a.status !== 'APPROVED' && a.status !== 'REJECTED';
        })
      );
    };
    fetchApplications();
  }, [mockData]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  // Dados do gráfico de desempenho
  const performanceData = {
    labels: ['Aprovadas', 'Pendentes', 'Rejeitadas', 'Em Análise'],
    datasets: [
      {
        label: 'Solicitações',
        data: [
          approved.length,
          pending.length,
          rejected.length,
          underReview.length,
        ],
        backgroundColor: [
          'rgba(34,197,94,0.7)',    // verde
          'rgba(59,130,246,0.7)',   // azul
          'rgba(239,68,68,0.7)',    // vermelho
          'rgba(251,191,36,0.7)',   // amarelo
        ],
        borderColor: [
          'rgba(34,197,94,1)',
          'rgba(59,130,246,1)',
          'rgba(239,68,68,1)',
          'rgba(251,191,36,1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const performanceOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Distribuição das Solicitações',
        font: { size: 18 }
      },
      datalabels: {
        anchor: 'end',
        align: 'end',
        color: '#222',
        font: { weight: 'bold', size: 14 },
        formatter: Math.round
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          font: { size: 14 }
        },
        title: {
          display: true,
          text: 'Quantidade',
          font: { size: 14 }
        }
      },
      x: {
        ticks: { font: { size: 14 } }
      }
    }
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
                <h2 className="text-2xl font-bold text-gray-900">Bom dia, {user?.full_name.split(' ')[0]}</h2>
                <p className="mt-1 text-gray-500 max-w-2xl">
                  Você tem <span className="font-medium text-primary-600">{pending.length}</span> solicitações pendentes,{' '}
                  <span className="font-medium text-green-600">{approved.length}</span> aprovadas,{' '}
                  <span className="font-medium text-red-600">{rejected.length}</span> rejeitadas e{' '}
                  <span className="font-medium text-warning-600">{slaWarnings.length}</span> alertas de SLA.
                </p>
              </div>
              <div className="mt-5 sm:mt-0">
                <Button
                  onClick={() => navigate('/staff/applications')}
                >
                  Ver todas as solicitações
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
                  <span className="text-xs font-medium text-green-600">
                    {applications.length > 0 ? Math.round((approved.length / applications.length) * 100) : 0}%
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Total de Solicitações</h3>
                <p className="text-3xl font-bold text-gray-900">{applications.length}</p>
                <div className="mt-1 text-sm text-gray-500">No mês atual</div>
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
                  <span className="text-xs font-medium text-red-600">
                    {applications.length > 0 ? Math.round((pending.length / applications.length) * 100) : 0}%
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Pendentes</h3>
                <p className="text-3xl font-bold text-gray-900">{pending.length}</p>
                <div className="mt-1 text-sm text-gray-500">Aguardando ação</div>
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
                  <span className="text-xs font-medium text-red-600">
                    {applications.length > 0 ? Math.round((slaWarnings.length / applications.length) * 100) : 0}%
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Alertas de SLA</h3>
                <p className="text-3xl font-bold text-gray-900">{slaWarnings.length}</p>
                <div className="mt-1 text-sm text-gray-500">Prazo se aproximando</div>
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
                  <span className="text-xs font-medium text-green-600">
                    {applications.length > 0 ? Math.round((approved.length / applications.length) * 100) : 0}%
                  </span>
                </div>
              </div>
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-500">Completadas</h3>
                <p className="text-3xl font-bold text-gray-900">{approved.length}</p>
                <div className="mt-1 text-sm text-gray-500">Este mês</div>
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
                  <CardTitle>Pendentes</CardTitle>
                  <CardDescription>
                    Solicitações que requerem sua atenção
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/staff/applications')}
                >
                  Ver todas
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full whitespace-nowrap">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Empresa
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Solicitação
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Valor
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Prazo
                      </th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pending.map((application) => {
                      // Calcula dias restantes para o deadline
                      let daysRemaining = '-';
                      if (application.deliver_date) {
                        const diff = Math.ceil((new Date(application.deliver_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                        daysRemaining = diff >= 0 ? diff : 0;
                      }
                      return (
                        <tr key={application.id} className="hover:bg-gray-50">
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="font-medium text-gray-900">{application.companyName}</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">{application.title || '-'}</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{formatCurrency(application.amount)}</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <ApplicationStatusBadge status={application.status} />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className={`text-sm font-medium ${daysRemaining <= 7 ? 'text-error-600' : 'text-gray-900'}`}>
                              {daysRemaining !== '-' ? `${daysRemaining} dias` : '-'}
                            </div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/staff/applications/${application.id}`)}
                            >
                              Analisar
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
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
                    <CardTitle>Alertas de SLA</CardTitle>
                    <CardDescription>
                      Solicitações com prazo se aproximando
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
                            <p className="text-sm text-gray-500">{warning.title || '-'}</p>
                          </div>
                          <div className="flex items-center">
                            <div className="flex items-center mr-4">
                              <AlertTriangle className="h-4 w-4 text-warning-500 mr-1" />
                              <span className="text-sm font-medium text-warning-600">
                                {(() => {
                                  const diff = Math.ceil((new Date(warning.deliver_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                                  return diff >= 0 ? `${diff} dias restantes` : 'Expirado';
                                })()}
                              </span>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/staff/applications/${warning.id}`)}
                            >
                              Ver
                            </Button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-6">
                    <CheckCircle className="mx-auto h-10 w-10 text-success-500" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum alerta de SLA</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Todas as solicitações estão dentro do prazo normal de processamento.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Desempenho Mensal</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center">
                  <div className="flex flex-col items-center w-full">
                    <Bar data={performanceData} options={performanceOptions} className="w-full" />
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