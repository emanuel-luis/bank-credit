import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import type { Action } from '../../api/types';
import { useHistory, useRequest, useTransition } from '../../hooks/useRequests';
import { errorMessage } from '../../lib/errors';
import { formatCnpj, formatDate, formatDateTime, formatMoney } from '../../lib/format';
import { DOCUMENT_LABELS, EVENT_LABELS } from '../../lib/labels';
import Button from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import ApplicationStatusBadge, { OverdueBadge } from './ApplicationStatusBadge';
import ReasonDialog from './ReasonDialog';

interface ActionConfig {
  label: string;
  variant: 'primary' | 'outline' | 'danger';
  /** Absent: the action is sent at once. Present: a dialog asks for the reason first. */
  dialog?: { title: string; required: boolean };
}

const ACTIONS: Partial<Record<Action, ActionConfig>> = {
  approve: { label: 'Aprovar', variant: 'primary' },
  return: { label: 'Devolver', variant: 'outline', dialog: { title: 'Devolver ao cliente', required: true } },
  reject: { label: 'Rejeitar', variant: 'danger', dialog: { title: 'Rejeitar solicitação', required: true } },
  resubmit: { label: 'Reenviar', variant: 'primary' },
  cancel: { label: 'Cancelar', variant: 'danger', dialog: { title: 'Cancelar solicitação', required: false } },
};

const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div>
    <dt className="text-xs uppercase text-gray-500">{label}</dt>
    <dd className="mt-1 text-sm text-gray-900">{children}</dd>
  </div>
);

interface RequestDetailPageProps {
  /** Route of the list page, used by the back link. */
  listPath: string;
  showClient?: boolean;
}

export default function RequestDetailPage({ listPath, showClient = false }: RequestDetailPageProps) {
  const id = Number(useParams().id);
  const request = useRequest(id);
  const history = useHistory(id);
  const transition = useTransition(id);
  const [pending, setPending] = useState<Action | null>(null);

  const r = request.data;
  if (request.isLoading) return <p className="text-gray-500">Carregando...</p>;
  if (!r) return <p className="text-red-600">{errorMessage(request.error)}</p>;

  const run = (action: Action, reason?: string) =>
    transition.mutate(
      { action, expected_seq: r.last_seq, ...(reason ? { reason } : {}) },
      { onSuccess: () => setPending(null) },
    );
  const click = (action: Action) => {
    transition.reset();
    if (ACTIONS[action]?.dialog) setPending(action);
    else run(action);
  };
  const pendingConfig = pending ? ACTIONS[pending] : undefined;
  const error = transition.isError ? errorMessage(transition.error) : null;

  return (
    <div className="space-y-6">
      <Link to={listPath} className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900">
        <ArrowLeft className="mr-1 h-4 w-4" /> Voltar
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Solicitação #{r.id}</h1>
          <ApplicationStatusBadge status={r.status} />
          {r.is_overdue && <OverdueBadge />}
        </div>
        <div className="flex gap-2">
          {r.allowed_actions.map((action) => {
            const cfg = ACTIONS[action];
            return cfg ? (
              <Button key={action} variant={cfg.variant} onClick={() => click(action)} disabled={transition.isPending}>
                {cfg.label}
              </Button>
            ) : null;
          })}
        </div>
      </div>

      {error && !pending && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      <Card>
        <CardContent className="pt-6">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {showClient && (
              <Field label="Empresa">
                {r.client.trade_name}
                <div className="text-xs text-gray-500">
                  {r.client.legal_name} - {formatCnpj(r.client.cnpj)}
                </div>
              </Field>
            )}
            <Field label="Valor">{formatMoney(r.amount)}</Field>
            <Field label="Prazo">{r.term_days} dias</Field>
            <Field label="Data de entrega">{formatDate(r.deliver_date)}</Field>
            <Field label="Finalidade">{r.purpose}</Field>
            <Field label="Etapa atual">{r.stage.name}</Field>
            <Field label="Setor">{r.sector.name}</Field>
            <Field label="Enviada em">{formatDateTime(r.submitted_at)}</Field>
            <Field label="Prazo da etapa (SLA)">
              {formatDateTime(r.sla_due_at)} {r.is_overdue && <OverdueBadge />}
            </Field>
            <Field label="Conclusão estimada">{formatDateTime(r.estimated_completion_at)}</Field>
            {r.closed_at && <Field label="Encerrada em">{formatDateTime(r.closed_at)}</Field>}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documentos declarados</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <ul className="space-y-1 text-sm">
            {r.documents.map((d) => (
              <li key={d.document_type}>
                {DOCUMENT_LABELS[d.document_type]}{' '}
                <span className="text-gray-500">({formatDateTime(d.declared_at)})</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Histórico</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          {history.isLoading && <p className="text-sm text-gray-500">Carregando...</p>}
          {history.isError && <p className="text-sm text-red-600">{errorMessage(history.error)}</p>}
          <ol className="space-y-4 border-l border-gray-200 pl-4">
            {history.data?.map((e) => (
              <li key={e.seq}>
                <p className="text-sm font-medium text-gray-900">{EVENT_LABELS[e.event_type]}</p>
                <p className="text-xs text-gray-500">
                  {formatDateTime(e.occurred_at)} - {e.stage.name} ({e.sector.name}) - {e.actor?.full_name ?? 'Sistema'}
                </p>
                {e.reason && <p className="mt-1 text-sm text-gray-700">Motivo: {e.reason}</p>}
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>

      {pending && pendingConfig?.dialog && (
        <ReasonDialog
          title={pendingConfig.dialog.title}
          confirmLabel={pendingConfig.label}
          required={pendingConfig.dialog.required}
          busy={transition.isPending}
          error={error}
          onConfirm={(reason) => run(pending, reason)}
          onClose={() => setPending(null)}
        />
      )}
    </div>
  );
}
