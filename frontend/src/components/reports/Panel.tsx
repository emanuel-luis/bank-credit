import type { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { errorMessage } from '../../lib/errors';
import { formatDateTime } from '../../lib/format';

interface PanelProps {
  title: string;
  /** Explains how the numbers are built (one or two sentences). */
  note: string;
  isLoading: boolean;
  error: unknown;
  isEmpty: boolean;
  sourceView?: string;
  generatedAt?: string;
  /** Text equivalent of the chart, shown on request. */
  table?: { head: string[]; rows: (string | number)[][] };
  /** Extra controls in the header, such as a week picker. */
  actions?: ReactNode;
  children: ReactNode;
}

export default function Panel({ title, note, isLoading, error, isEmpty, sourceView, generatedAt, table, actions, children }: PanelProps) {
  let body: ReactNode;
  if (error) {
    body = <p role="alert" className="py-12 text-center text-sm text-error-600">{errorMessage(error)}</p>;
  } else if (isLoading) {
    body = <p className="py-12 text-center text-sm text-gray-500">Carregando…</p>;
  } else if (isEmpty) {
    body = <p className="py-12 text-center text-sm text-gray-500">Sem dados no período</p>;
  } else {
    body = <div className="h-72">{children}</div>;
  }
  return (
    <Card>
      <CardHeader className="flex flex-wrap items-center justify-between gap-2">
        <CardTitle>{title}</CardTitle>
        {actions}
      </CardHeader>
      <CardContent>
        {body}
        {table && !error && !isLoading && !isEmpty && (
          <details className="mt-3 text-sm text-gray-700">
            <summary className="cursor-pointer text-primary-600">Ver tabela</summary>
            <div className="mt-2 max-h-64 overflow-auto">
              <table className="min-w-full text-left text-xs">
                <thead className="sticky top-0 bg-white text-gray-500">
                  <tr>{table.head.map((h) => <th key={h} className="px-2 py-1 font-medium">{h}</th>)}</tr>
                </thead>
                <tbody>
                  {table.rows.map((row, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      {row.map((cell, j) => <td key={j} className="px-2 py-1">{cell}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}
        <p className="mt-3 text-xs text-gray-500">
          {note}
          {sourceView && generatedAt && ` Fonte: ${sourceView}, gerado em ${formatDateTime(generatedAt)}.`}
        </p>
      </CardContent>
    </Card>
  );
}
