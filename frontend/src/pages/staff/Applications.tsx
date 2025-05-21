import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import ApplicationCard from '../../components/loan/ApplicationCard';
import Button from '../../components/ui/Button';
import { useMockApplication } from '../../context/mockdata';

const PAGE_SIZE = 6;

export default function Applications() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const { mockData } = useMockApplication();

  // Estados para contagem dinâmica
  const [total, setTotal] = useState(0);
  const [pendentes, setPendentes] = useState(0);
  const [aprovadas, setAprovadas] = useState(0);
  const [rejeitadas, setRejeitadas] = useState(0);

  useEffect(() => {
    const fetchApplications = async () => {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://127.0.0.1:8000/requests/all', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) {
        setApplications([]);
        setTotal(0);
        setPendentes(0);
        setAprovadas(0);
        setRejeitadas(0);
        setLoading(false);
        return;
      }
      const data = await response.json();

      // Sempre prioriza status e campos do mockData
      const enriched = data.map((app: any) => ({
        ...app,
        ...(mockData[app.id] || {}),
        status: mockData[app.id]?.status || app.status,
      }));

      setApplications(enriched);

      // Contagens dinâmicas
      setTotal(enriched.length);
      setPendentes(enriched.filter((a: any) => a.status === 'PENDING').length);
      setAprovadas(enriched.filter((a: any) => a.status === 'APPROVED').length);
      setRejeitadas(enriched.filter((a: any) => a.status === 'REJECTED').length);

      setLoading(false);
    };
    fetchApplications();
  }, [mockData]);

  // Paginação
  const totalPages = Math.ceil(applications.length / PAGE_SIZE);
  const paginatedApps = applications.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Solicitações de Empréstimo</h1>
      </div>

      {/* Cards de contagem */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-2">
        <div className="bg-white rounded shadow p-4 flex flex-col items-center">
          <span className="text-sm text-gray-500">Total</span>
          <span className="text-2xl font-bold">{total}</span>
        </div>
        <div className="bg-yellow-50 rounded shadow p-4 flex flex-col items-center">
          <span className="text-sm text-yellow-700">Pendentes</span>
          <span className="text-2xl font-bold text-yellow-700">{pendentes}</span>
        </div>
        <div className="bg-green-50 rounded shadow p-4 flex flex-col items-center">
          <span className="text-sm text-green-700">Aprovadas</span>
          <span className="text-2xl font-bold text-green-700">{aprovadas}</span>
        </div>
        <div className="bg-red-50 rounded shadow p-4 flex flex-col items-center">
          <span className="text-sm text-red-700">Rejeitadas</span>
          <span className="text-2xl font-bold text-red-700">{rejeitadas}</span>
        </div>
      </div>

      <Card className="overflow-hidden">
        <div className="p-6">
          <div className="space-y-4">
            {loading ? (
              <ApplicationCard
                id="placeholder"
                title="Carregando..."
                status="pending"
                amount={0}
                department="Carregando..."
                submittedAt={new Date()}
                onViewDetails={() => {}}
                central="Carregando..."
              />
            ) : paginatedApps.length === 0 ? (
              <div className="text-center text-gray-500 py-10">Nenhuma solicitação encontrada.</div>
            ) : (
              paginatedApps.map((application) => (
                <ApplicationCard
                  key={application.id}
                  {...application}
                  status={application.status}
                  companyName={application.companyName || '-'}
                  contactName={application.contactName}
                  cnpj={application.cnpj}
                  purpose={application.purpose}
                  term={application.term}
                  submittedAt={application.created_at}
                  central={application.central || '-'}
                  onViewDetails={(id) => navigate(`/staff/applications/${id}`)}
                />
              ))
            )}
          </div>
          {/* Paginação */}
          {!loading && totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <span className="mx-2 text-sm text-gray-700">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Próxima
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}