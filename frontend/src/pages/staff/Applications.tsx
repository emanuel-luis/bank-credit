import { useState } from 'react';
import { Card } from '../../components/ui/Card';
import Pagination from '../../components/loan/Pagination';
import RequestTable from '../../components/loan/RequestTable';
import { useQueueScope } from '../../hooks/useQueueScope';
import { useRequests, useWorkflow } from '../../hooks/useRequests';
import type { Status } from '../../api/types';
import { errorMessage } from '../../lib/errors';
import { STATUSES, STATUS_LABELS } from '../../lib/labels';

const LIMIT = 15;
const selectClass = 'rounded-md border border-gray-300 px-3 py-2 text-sm';

export default function StaffApplications() {
  const { scope, basePath } = useQueueScope();
  const workflow = useWorkflow();
  const [stage, setStage] = useState('');
  const [overdue, setOverdue] = useState(false);
  const [status, setStatus] = useState<Status | ''>('');
  const [offset, setOffset] = useState(0);
  const { data, isError, error } = useRequests({
    scope,
    stage: stage || undefined,
    overdue: overdue || undefined,
    // The sector queue is always the open work; only admin can browse other statuses.
    status: scope === 'all' ? status || undefined : undefined,
    limit: LIMIT,
    offset,
  });
  const reset = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setOffset(0);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">{scope === 'all' ? 'Solicitações' : 'Fila do setor'}</h1>

      <div className="flex flex-wrap items-center gap-4">
        <label className="text-sm text-gray-700">
          Etapa{' '}
          <select value={stage} onChange={(e) => reset(setStage)(e.target.value)} className={selectClass}>
            <option value="">Todas</option>
            {workflow.data?.stages.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        {scope === 'all' && (
          <label className="text-sm text-gray-700">
            Status{' '}
            <select value={status} onChange={(e) => reset(setStatus)(e.target.value as Status | '')} className={selectClass}>
              <option value="">Todos</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={overdue} onChange={(e) => reset(setOverdue)(e.target.checked)} />
          Somente atrasadas
        </label>
      </div>

      <Card>
        {isError && <p className="p-6 text-sm text-red-600">{errorMessage(error)}</p>}
        {data && (
          <>
            <RequestTable items={data.items} basePath={basePath} showClient />
            <Pagination offset={offset} limit={LIMIT} total={data.total} onChange={setOffset} />
          </>
        )}
      </Card>
    </div>
  );
}
