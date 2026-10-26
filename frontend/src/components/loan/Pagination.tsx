import Button from '../ui/Button';

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}

export default function Pagination({ offset, limit, total, onChange }: PaginationProps) {
  if (total <= limit) return null;
  const last = Math.min(offset + limit, total);
  return (
    <div className="flex items-center justify-between px-4 py-3 text-sm text-gray-600">
      <span>
        {offset + 1} a {last} de {total}
      </span>
      <div className="flex gap-2">
        <Button size="sm" variant="outline" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>
          Anterior
        </Button>
        <Button size="sm" variant="outline" disabled={last >= total} onClick={() => onChange(offset + limit)}>
          Próxima
        </Button>
      </div>
    </div>
  );
}
