import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import ApplicationStatusBadge from '../../components/loan/ApplicationStatusBadge';
import Button from '../../components/ui/Button';
import { useMockApplication } from '../../context/mockdata';

// Diálogo de confirmação em português
function ConfirmDialog({
  open,
  onConfirm,
  onCancel,
  newStatusLabel,
}: {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  newStatusLabel: string;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded shadow-lg p-6 w-full max-w-xs">
        <h2 className="text-lg font-semibold mb-2">Confirmar alteração</h2>
        <p className="mb-4">
          Tem certeza que deseja alterar o status para{' '}
          <span className="font-bold">{newStatusLabel}</span>?
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancelar
          </Button>
          <Button size="sm" onClick={onConfirm}>
            Confirmar
          </Button>
        </div>
      </div>
    </div>
  );
}

const STATUS_OPTIONS = [
  { value: 'Pendente'},
  { value: 'Aprovado'},
  { value: 'Rejeitado'},
  { value: 'Em análise'},
  { value: 'Checagem de documento'},
];

const STAGE_OPTIONS = [
  { value: 'Checagem', label: 'Checagem' },
  { value: 'Triagem', label: 'Triagem' },
  { value: 'Analise', label: 'Análise' },
  { value: 'Criacao de Instrumento', label: 'Criação de instrumento' },
  { value: 'Central de Desembolso', label: 'Central de Desembolso' },
];

export default function ApplicationDetails() {
  const { id } = useParams();
  const [application, setApplication] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string>('PENDING');
  const [stage, setStage] = useState<string>('checagem');
  const [saving, setSaving] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);
  const [pendingStage, setPendingStage] = useState<string | null>(null);
  const { getMockData, setMockData } = useMockApplication();

  useEffect(() => {
    const fetchApplication = async () => {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://127.0.0.1:8000/requests/${id}/`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        setLoading(false);
        return;
      }
      const data = await response.json();

      // Busca dados mockados do contexto
      const mock = getMockData ? getMockData(Number(id)) : {};
      setApplication({
        ...data,
        ...mock,
      });
      setStatus(mock?.status || data.status || 'PENDING');
      setStage(mock?.stage || 'checagem');
      setLoading(false);
    };
    fetchApplication();
  }, [id, getMockData]);

  // Só altera o valor local, não abre dialog
  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPendingStatus(e.target.value);
  };

  // Só altera o valor local, não abre dialog
  const handleStageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPendingStage(e.target.value);
  };

  // O dialog só abre ao clicar em "Salvar" E se o status foi alterado
  const handleSaveClick = () => {
    if (pendingStatus && pendingStatus !== status) {
      setShowDialog(true);
    } else {
      // Se só a etapa mudou, salva direto sem dialog
      handleConfirmStatus();
    }
  };

 const handleConfirmStatus = async () => {
    setSaving(true);
    setShowDialog(false);
    const token = localStorage.getItem('access_token');
    if (pendingStatus && pendingStatus !== status) {
      await fetch(`http://127.0.0.1:8000/requests/${id}/status`, {
        method: 'PATCH',
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: pendingStatus }),
      });
      setStatus(pendingStatus);
    }
    // Salva etapa e departamento no mockData
    const newStage = pendingStage || stage;
    setStage(newStage);
    // No staff/ApplicationDetails.tsx, ao salvar no mockData:
    setMockData(Number(id), {
      ...application,
      status: pendingStatus || status,
      stage: newStage,
      departamento: newStage // <-- salva como 'departamento' também
    });
    setSaving(false);
    setPendingStatus(null);
    setPendingStage(null);
  };

  const handleCancelDialog = () => {
    setShowDialog(false);
    setPendingStatus(null);
    setPendingStage(null);
  };

  if (loading || !application) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-semibold text-gray-900">Detalhes da Solicitação</h1>
          <ApplicationStatusBadge status="pending" />
        </div>
        <Card>
          <div className="p-6">Carregando...</div>
        </Card>
      </div>
    );
  }

  const newStatusLabel =
    STATUS_OPTIONS.find((opt) => opt.value === (pendingStatus ?? status))?.label || '';

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={showDialog}
        onConfirm={handleConfirmStatus}
        onCancel={handleCancelDialog}
        newStatusLabel={newStatusLabel}
      />

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Detalhes da Solicitação</h1>
        <ApplicationStatusBadge status={status} />
      </div>

      <Card>
        <div className="p-6">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Solicitação #{id}</h2>
              <p className="mt-1 text-sm text-gray-500">
                Visualize e processe os detalhes da solicitação
              </p>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Nome do Solicitante</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {application.applicantName || application.contactName || '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Nome da Empresa</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {application.companyName || application.company_name || '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Data da Solicitação</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {application.created_at
                      ? new Date(application.created_at).toLocaleDateString('pt-BR')
                      : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Valor do Empréstimo</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {application.amount
                      ? application.amount.toLocaleString('pt-BR', {
                          style: 'currency',
                          currency: 'BRL',
                        })
                      : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Prazo (meses)</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {application.term ? `${application.term} meses` : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1 text-sm text-gray-900 flex items-center">
                    <select
                      className="border rounded px-2 py-1"
                      value={pendingStatus ?? status}
                      onChange={handleStatusChange}
                      disabled={saving}
                    >
                      {STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Etapa da Solicitação</dt>
                  <dd className="mt-1 text-sm text-gray-900 flex items-center">
                    <select
                      className="border rounded px-2 py-1"
                      value={pendingStage ?? stage}
                      onChange={handleStageChange}
                      disabled={saving}
                    >
                      {STAGE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </dd>
                </div>
              </dl>
              <div className="mt-4 flex justify-end">
                <Button
                  className="ml-2"
                  size="sm"
                  onClick={handleSaveClick}
                  disabled={saving || (!pendingStatus && !pendingStage)}
                >
                  {saving ? 'Salvando...' : 'Salvar'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}