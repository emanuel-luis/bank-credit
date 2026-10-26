import { Link } from 'react-router-dom';
import type { RequestSummary } from '../../api/types';
import { formatDateTime, formatMoney } from '../../lib/format';
import ApplicationStatusBadge, { OverdueBadge } from './ApplicationStatusBadge';

interface RequestTableProps {
  items: RequestSummary[];
  /** Route prefix of the detail page, e.g. "/customer/applications". */
  basePath: string;
  showClient?: boolean;
}

export default function RequestTable({ items, basePath, showClient = false }: RequestTableProps) {
  if (items.length === 0) {
    return <p className="px-6 py-8 text-center text-sm text-gray-500">Nenhuma solicitação encontrada.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
          <tr>
            <th className="px-4 py-3">Nº</th>
            {showClient && <th className="px-4 py-3">Empresa</th>}
            <th className="px-4 py-3">Valor</th>
            <th className="px-4 py-3">Finalidade</th>
            <th className="px-4 py-3">Etapa</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Prazo (SLA)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {items.map((r) => (
            <tr key={r.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <Link to={`${basePath}/${r.id}`} className="font-medium text-primary-600 hover:underline">
                  #{r.id}
                </Link>
              </td>
              {showClient && <td className="px-4 py-3">{r.client.trade_name}</td>}
              <td className="px-4 py-3 whitespace-nowrap">{formatMoney(r.amount)}</td>
              <td className="px-4 py-3 max-w-xs truncate">{r.purpose}</td>
              <td className="px-4 py-3">
                {r.stage.name}
                <div className="text-xs text-gray-500">{r.sector.name}</div>
              </td>
              <td className="px-4 py-3">
                <ApplicationStatusBadge status={r.status} />
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                {formatDateTime(r.sla_due_at)} {r.is_overdue && <OverdueBadge />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
