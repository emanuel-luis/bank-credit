const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
const dateTime = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
const date = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' });

/** Formats a decimal string such as "125000.00". Float precision is enough for display. */
export function formatMoney(value: string): string {
  const n = Number(value);
  return Number.isFinite(n) ? brl.format(n) : value;
}

/** ISO UTC timestamp to pt-BR date and time in the browser's time zone. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateTime.format(d);
}

/** Calendar date ("2026-11-01") shown as-is, without a time zone shift. */
export function formatDate(day: string | null | undefined): string {
  if (!day) return '-';
  const [y, m, d] = day.split('-').map(Number);
  if (!y || !m || !d) return day;
  return date.format(new Date(y, m - 1, d));
}

/** CNPJ (numeric or alphanumeric, 14 characters) as AA.AAA.AAA/AAAA-DD. Other input is returned as-is. */
export function formatCnpj(value: string | null | undefined): string {
  if (!value) return '-';
  const v = value.toUpperCase();
  if (!/^[0-9A-Z]{12}\d{2}$/.test(v)) return value;
  return `${v.slice(0, 2)}.${v.slice(2, 5)}.${v.slice(5, 8)}/${v.slice(8, 12)}-${v.slice(12)}`;
}
