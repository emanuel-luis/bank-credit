import { Card, CardContent } from './Card';

interface StatProps {
  label: string;
  /** undefined while the count is loading. */
  value: number | undefined;
  tone?: 'default' | 'danger';
}

export default function Stat({ label, value, tone = 'default' }: StatProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-gray-500">{label}</p>
        <p className={`mt-1 text-3xl font-semibold ${tone === 'danger' ? 'text-red-600' : 'text-gray-900'}`}>
          {value ?? '-'}
        </p>
      </CardContent>
    </Card>
  );
}
