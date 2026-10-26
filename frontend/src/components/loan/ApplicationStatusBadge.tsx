import { twMerge } from 'tailwind-merge';
import type { Status } from '../../api/types';
import { STATUS_LABELS } from '../../lib/labels';

const STATUS_COLORS: Record<Status, string> = {
  IN_REVIEW: 'bg-amber-100 text-amber-700',
  RETURNED: 'bg-orange-100 text-orange-700',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  CANCELLED: 'bg-gray-100 text-gray-700',
  EXPIRED: 'bg-gray-100 text-gray-700',
};

interface ApplicationStatusBadgeProps {
  status: Status;
  className?: string;
}

export default function ApplicationStatusBadge({ status, className }: ApplicationStatusBadgeProps) {
  return (
    <span
      className={twMerge(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        STATUS_COLORS[status],
        className
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

export function OverdueBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
      Atrasada
    </span>
  );
}
