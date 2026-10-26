import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import Button from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import Pagination from '../../components/loan/Pagination';
import RequestTable from '../../components/loan/RequestTable';
import { useRequests } from '../../hooks/useRequests';
import type { Status } from '../../api/types';
import { errorMessage } from '../../lib/errors';
import { STATUSES, STATUS_LABELS } from '../../lib/labels';

const LIMIT = 10;

export default function CustomerApplications() {
  const [status, setStatus] = useState<Status | ''>('');
  const [offset, setOffset] = useState(0);
  const { data, isError, error } = useRequests({
    scope: 'mine',
    status: status || undefined,
    limit: LIMIT,
    offset,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Minhas solicitações</h1>
        <Link to="/customer/applications/new">
          <Button leftIcon={<Plus className="h-4 w-4" />}>Nova solicitação</Button>
        </Link>
      </div>

      <div>
        <label htmlFor="status" className="mr-2 text-sm text-gray-700">
          Status
        </label>
        <select
          id="status"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as Status | '');
            setOffset(0);
          }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      <Card>
        {isError && <p className="p-6 text-sm text-red-600">{errorMessage(error)}</p>}
        {data && (
          <>
            <RequestTable items={data.items} basePath="/customer/applications" />
            <Pagination offset={offset} limit={LIMIT} total={data.total} onChange={setOffset} />
          </>
        )}
      </Card>
    </div>
  );
}
