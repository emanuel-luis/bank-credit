import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import Button from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import type { DocumentType } from '../../api/types';
import { useCreateRequest } from '../../hooks/useRequests';
import { errorMessage } from '../../lib/errors';
import { formatDateTime, formatMoney } from '../../lib/format';
import { ALL_DOCUMENTS, DOCUMENT_LABELS, REQUIRED_DOCUMENTS } from '../../lib/labels';

interface FormData {
  amount: string;
  purpose: string;
  term_days: number;
  deliver_date: string;
  documents: DocumentType[];
}

const inputClass = 'mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm';

export default function NewApplication() {
  const create = useCreateRequest();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormData>({ defaultValues: { documents: [] } });
  const selected = watch('documents');
  const missing = REQUIRED_DOCUMENTS.some((d) => !selected.includes(d));

  const onSubmit = (data: FormData) =>
    create.mutate({
      amount: data.amount.trim().replace(',', '.'),
      purpose: data.purpose.trim(),
      term_days: Number(data.term_days),
      deliver_date: data.deliver_date,
      documents: data.documents,
    });

  if (create.data) {
    const r = create.data;
    return (
      <Card>
        <CardContent className="space-y-3 pt-6">
          <h1 className="text-2xl font-bold text-gray-900">Solicitação #{r.id} enviada</h1>
          <p className="text-sm text-gray-700">
            Valor {formatMoney(r.amount)}. A solicitação está em {r.stage.name}, no setor {r.sector.name}, com prazo até{' '}
            {formatDateTime(r.sla_due_at)}.
          </p>
          <div className="flex gap-2">
            <Link to={`/customer/applications/${r.id}`}>
              <Button>Ver solicitação</Button>
            </Link>
            <Link to="/customer/applications">
              <Button variant="outline">Minhas solicitações</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Nova solicitação de crédito</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
        <Card>
          <CardHeader>
            <CardTitle>Dados do crédito</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                Valor (R$)
              </label>
              <input
                id="amount"
                inputMode="decimal"
                placeholder="125000,00"
                className={inputClass}
                {...register('amount', { required: true, pattern: /^\d+([.,]\d{1,2})?$/ })}
              />
              {errors.amount && <p className="mt-1 text-xs text-red-600">Informe um valor positivo, como 125000,00.</p>}
            </div>
            <div>
              <label htmlFor="purpose" className="block text-sm font-medium text-gray-700">
                Finalidade
              </label>
              <textarea
                id="purpose"
                rows={3}
                maxLength={500}
                className={inputClass}
                {...register('purpose', { required: true, validate: (v) => v.trim() !== '' })}
              />
              {errors.purpose && <p className="mt-1 text-xs text-red-600">Informe a finalidade.</p>}
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="term_days" className="block text-sm font-medium text-gray-700">
                  Prazo (dias)
                </label>
                <input
                  id="term_days"
                  type="number"
                  min={1}
                  className={inputClass}
                  {...register('term_days', { required: true, min: 1 })}
                />
                {errors.term_days && <p className="mt-1 text-xs text-red-600">Informe um prazo em dias.</p>}
              </div>
              <div>
                <label htmlFor="deliver_date" className="block text-sm font-medium text-gray-700">
                  Data de entrega
                </label>
                <input id="deliver_date" type="date" className={inputClass} {...register('deliver_date', { required: true })} />
                {errors.deliver_date && <p className="mt-1 text-xs text-red-600">Informe a data de entrega.</p>}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Documentos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 pt-4">
            <p className="text-sm text-gray-500">Declare os documentos que a empresa possui. Nenhum arquivo é enviado.</p>
            {ALL_DOCUMENTS.map((d) => (
              <label key={d} className="flex items-center gap-2 text-sm text-gray-800">
                <input type="checkbox" value={d} {...register('documents')} />
                {DOCUMENT_LABELS[d]}
              </label>
            ))}
            {missing && <p className="text-xs text-gray-500">Marque os quatro documentos obrigatórios para enviar.</p>}
          </CardContent>
        </Card>

        {create.isError && (
          <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            {errorMessage(create.error)}
          </div>
        )}
        <div className="flex justify-end gap-2">
          <Link to="/customer/applications">
            <Button type="button" variant="outline">
              Cancelar
            </Button>
          </Link>
          <Button type="submit" isLoading={create.isPending} disabled={missing}>
            Enviar solicitação
          </Button>
        </div>
      </form>
    </div>
  );
}
