import { describe, expect, it } from 'vitest';
import { dayLabel, pivotBreachRate, sectorOrder, stageBars, throughputByDay, weekLabel, weeksOf, defaultWeek } from './reports';

describe('labels', () => {
  it('formats days and weeks in pt-BR', () => {
    expect(dayLabel('2026-11-02')).toBe('02 nov');
    expect(dayLabel('2026-02-09')).toBe('09 fev');
    expect(weekLabel('2026-03-30')).toBe('sem. 30 mar');
  });
});

describe('pivotBreachRate', () => {
  const rows = [
    { sector_code: 'B', week_start: '2026-10-05', closed: 4, breached: 1, breach_rate: '0.2500' },
    { sector_code: 'A', week_start: '2026-10-12', closed: 10, breached: 2, breach_rate: '0.2000' },
    { sector_code: 'A', week_start: '2026-10-05', closed: 5, breached: 0, breach_rate: '0.0000' },
  ];
  it('aligns sectors on the union of weeks, in percent', () => {
    const { weeks, series } = pivotBreachRate(rows);
    expect(weeks).toEqual(['2026-10-05', '2026-10-12']);
    expect(series.map((s) => s.sector)).toEqual(['A', 'B']);
    expect(series[0].rate).toEqual([0, 20]);
    expect(series[1].rate).toEqual([25, null]);
    expect(series[1].closed).toEqual([4, 0]);
    expect(series[0].breached).toEqual([0, 2]);
  });
  it('returns nothing for no rows', () => {
    expect(pivotBreachRate([])).toEqual({ weeks: [], series: [] });
  });
});

describe('time in stage', () => {
  const row = (stage_code: string, sector_code: string, week_start: string, p50_h: string, p90_h: string) => ({
    stage_code,
    sector_code,
    week_start,
    n: 3,
    avg_h: '1.00',
    p50_h,
    p90_h,
  });
  const rows = [
    row('s2', 'A', '2026-10-12', '10.50', '30.00'),
    row('s1', 'A', '2026-10-12', '2.00', '5.25'),
    row('s1', 'A', '2026-10-05', '9.00', '9.00'),
  ];
  it('lists weeks newest first', () => {
    expect(weeksOf(rows)).toEqual(['2026-10-12', '2026-10-05']);
  });
  it('takes one week only, in stage order, with names', () => {
    const bars = stageBars(rows, '2026-10-12', { s1: 'Triagem', s2: 'Análise' }, { A: 'Setor A' }, ['s1', 's2']);
    expect(bars.map((b) => [b.label, b.p50, b.p90])).toEqual([
      ['Triagem', 2, 5.25],
      ['Análise', 10.5, 30],
    ]);
  });
  it('adds the sector to the label when several share the week', () => {
    const bars = stageBars([row('s1', 'A', 'w', '1', '2'), row('s1', 'B', 'w', '3', '4')], 'w', {}, { B: 'Setor B' }, ['s1']);
    expect(bars.map((b) => b.label)).toEqual(['s1 (A)', 's1 (Setor B)']);
  });
});

describe('throughputByDay', () => {
  it('sums sectors per day', () => {
    const base = { entered: 0, approved: 0, returned: 0, rejected: 0, cancelled: 0, expired: 0 };
    const { days, totals } = throughputByDay([
      { ...base, sector_code: 'A', day: '2026-10-02', entered: 2, approved: 1 },
      { ...base, sector_code: 'B', day: '2026-10-02', entered: 1, expired: 4 },
      { ...base, sector_code: 'A', day: '2026-10-01', rejected: 3 },
    ]);
    expect(days).toEqual(['2026-10-01', '2026-10-02']);
    expect(totals.entered).toEqual([0, 3]);
    expect(totals.approved).toEqual([0, 1]);
    expect(totals.rejected).toEqual([3, 0]);
    expect(totals.expired).toEqual([0, 4]);
  });
});

describe('sectorOrder', () => {
  it('is sorted and unique', () => {
    expect(sectorOrder(['b', 'a'], ['c', 'a'])).toEqual(['a', 'b', 'c']);
  });
});

describe('defaultWeek', () => {
  const weeks = ['2026-10-26', '2026-10-19', '2026-10-12'];
  it('skips the current week that has not ended', () => {
    expect(defaultWeek(weeks, '2026-10-28')).toBe('2026-10-19');
  });
  it('takes the newest week once it has ended', () => {
    expect(defaultWeek(weeks, '2026-11-02')).toBe('2026-10-26');
  });
  it('falls back to the newest week and handles no data', () => {
    expect(defaultWeek(['2026-10-26'], '2026-10-27')).toBe('2026-10-26');
    expect(defaultWeek([], '2026-10-27')).toBe('');
  });
});
