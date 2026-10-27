import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle } from '../../components/ui/Card';
import Stat from '../../components/ui/Stat';
import RequestTable from '../../components/loan/RequestTable';
import { useAuth } from '../../contexts/AuthContext';
import { useQueueScope } from '../../hooks/useQueueScope';
import { useRequests, useWorkflow } from '../../hooks/useRequests';
import type { Scope } from '../../api/types';
import { errorMessage } from '../../lib/errors';

const DAY_MS = 24 * 60 * 60 * 1000;

function StageStat({ scope, code, name }: { scope: Scope; code: string; name: string }) {
  const { data } = useRequests({ scope, status: 'IN_REVIEW', stage: code, limit: 1 });
  return <Stat label={name} value={data?.total} />;
}

export default function StaffDashboard() {
  const { user } = useAuth();
  const { scope, basePath } = useQueueScope();
  const workflow = useWorkflow();
  const inReview = useRequests({ scope, status: 'IN_REVIEW', limit: 1 });
  const overdue = useRequests({ scope, overdue: true, limit: 1 });
  // Only the sector queue is ordered by SLA (admin gets submitted_at desc), so sort here.
  // One page of 100 holds everything due soon unless the backlog is larger.
  const next = useRequests({ scope, status: 'IN_REVIEW', limit: 100 });
  const bySla = next.data?.items
    .slice()
    .sort((a, b) => (a.sla_due_at ?? '9999').localeCompare(b.sla_due_at ?? '9999'));

  // Measured from when the queue was fetched, like is_overdue, so render stays pure.
  const dueSoon = bySla?.filter(
    (r) => !r.is_overdue && r.sla_due_at && new Date(r.sla_due_at).getTime() - next.dataUpdatedAt <= DAY_MS,
  ).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Olá, {user?.full_name.split(' ')[0]}</h1>
        <p className="text-sm text-gray-500">
          {scope === 'all' ? 'Todas as solicitações' : (user?.employee?.sector?.name ?? 'Fila do setor')}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat label="Em análise" value={inReview.data?.total} />
        <Stat label="Atrasadas" value={overdue.data?.total} tone="danger" />
        <Stat label="Vencem em 24 h" value={dueSoon} />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">Em análise por etapa</h2>
        {workflow.isError && <p className="text-sm text-red-600">{errorMessage(workflow.error)}</p>}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {workflow.data?.stages.map((s) => (
            <StageStat key={s.code} scope={scope} code={s.code} name={s.name} />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Próximas a vencer</CardTitle>
          <Link to={basePath} className="text-sm text-primary-600 hover:underline">
            Ver fila
          </Link>
        </CardHeader>
        {next.isError && <p className="p-6 text-sm text-red-600">{errorMessage(next.error)}</p>}
        {bySla && <RequestTable items={bySla.slice(0, 5)} basePath={basePath} showClient />}
      </Card>
    </div>
  );
}
