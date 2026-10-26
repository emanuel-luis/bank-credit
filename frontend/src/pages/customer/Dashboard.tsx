import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import Button from '../../components/ui/Button';
import Stat from '../../components/ui/Stat';
import { Card, CardHeader, CardTitle } from '../../components/ui/Card';
import RequestTable from '../../components/loan/RequestTable';
import { useAuth } from '../../contexts/AuthContext';
import { useRequests } from '../../hooks/useRequests';
import { errorMessage } from '../../lib/errors';

// limit=1 is enough to read `total` for a count.
const mine = { scope: 'mine', limit: 1 } as const;

export default function CustomerDashboard() {
  const { user } = useAuth();
  const all = useRequests(mine);
  const inReview = useRequests({ ...mine, status: 'IN_REVIEW' });
  const returned = useRequests({ ...mine, status: 'RETURNED' });
  const approved = useRequests({ ...mine, status: 'APPROVED' });
  const recent = useRequests({ scope: 'mine', limit: 5 });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Olá, {user?.full_name.split(' ')[0]}</h1>
          <p className="text-sm text-gray-500">{user?.client?.trade_name}</p>
        </div>
        <Link to="/customer/applications/new">
          <Button leftIcon={<Plus className="h-4 w-4" />}>Nova solicitação</Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Total" value={all.data?.total} />
        <Stat label="Em análise" value={inReview.data?.total} />
        <Stat label="Devolvidas" value={returned.data?.total} />
        <Stat label="Aprovadas" value={approved.data?.total} />
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Solicitações recentes</CardTitle>
          <Link to="/customer/applications" className="text-sm text-primary-600 hover:underline">
            Ver todas
          </Link>
        </CardHeader>
        {recent.isError && <p className="p-6 text-sm text-red-600">{errorMessage(recent.error)}</p>}
        {recent.data && <RequestTable items={recent.data.items} basePath="/customer/applications" />}
      </Card>
    </div>
  );
}
