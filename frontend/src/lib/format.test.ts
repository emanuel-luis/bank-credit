import { describe, expect, it } from 'vitest';
import { formatCnpj, formatDate, formatDateTime, formatMoney } from './format';

const nbsp = (s: string) => s.replace(/\u00a0/g, ' ');

describe('format', () => {
  it('formats a decimal string as BRL', () => {
    expect(nbsp(formatMoney('125000.00'))).toBe('R$ 125.000,00');
    expect(nbsp(formatMoney('0.50'))).toBe('R$ 0,50');
  });

  it('returns the input when the money is not a number', () => {
    expect(formatMoney('abc')).toBe('abc');
  });

  it('shows a calendar date without a time zone shift', () => {
    expect(formatDate('2026-11-01')).toBe('01/11/2026');
    expect(formatDate(null)).toBe('-');
  });

  it('formats an ISO timestamp as pt-BR date and time', () => {
    expect(formatDateTime('2026-11-01T12:00:00Z')).toMatch(/^\d{2}\/\d{2}\/\d{4},? \d{2}:\d{2}$/);
    expect(formatDateTime(undefined)).toBe('-');
  });

  it('formats numeric and alphanumeric CNPJs', () => {
    expect(formatCnpj('88125205000144')).toBe('88.125.205/0001-44');
    expect(formatCnpj('12ABC34501DE55')).toBe('12.ABC.345/01DE-55');
    expect(formatCnpj('12abc34501de55')).toBe('12.ABC.345/01DE-55');
  });

  it('leaves malformed CNPJs untouched and shows a dash when empty', () => {
    expect(formatCnpj('123')).toBe('123');
    expect(formatCnpj('1234567890123A')).toBe('1234567890123A');
    expect(formatCnpj(null)).toBe('-');
  });
});
