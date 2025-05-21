import { twMerge } from 'tailwind-merge';

export type ApplicationStatus =
  | 'Enviado'
  | 'Checagem de Documentos'
  | 'Em análise'
  | 'Documentos Pendentes'
  | 'Pendente'
  | 'Aprovado'
  | 'Rejeitado'

interface ApplicationStatusBadgeProps {
  status: ApplicationStatus | string;
  className?: string;
}

const statusConfig: Record<string, { label: string; bgColor: string; textColor: string }> = {
  draft: {
    label: 'Draft',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-700',
  },
  submitted: {
    label: 'Submitted',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
  },
  document_check: {
    label: 'Document Check',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-700',
  },
  under_review: {
    label: 'Under Review',
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-700',
  },
  pending_documents: {
    label: 'Pending Documents',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-700',
  },
  approved: {
    label: 'Approved',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
  },
  rejected: {
    label: 'Rejected',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
  },
  escalated: {
    label: 'Escalated',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-700',
  },
  // Suporte para status em caixa alta vindos do backend
  PENDING: {
    label: 'Pendente',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-700',
  },
  APPROVED: {
    label: 'Aprovado',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
  },
  REJECTED: {
    label: 'Rejeitado',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
  },
};

export default function ApplicationStatusBadge({
  status,
  className,
}: ApplicationStatusBadgeProps) {
  const config = statusConfig[status] || statusConfig['Pendente'];

  return (
    <span
      className={twMerge(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.bgColor,
        config.textColor,
        className
      )}
    >
      {config.label}
    </span>
  );
}