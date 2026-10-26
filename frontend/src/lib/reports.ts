import type { SlaBreachRateRow, ThroughputRow, TimeInStageRow } from '../api/analytics';

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

/** API decimals arrive as strings; convert only to plot them. */
export const toNumber = (value: string): number => Number(value);

/** "2026-11-02" to "02 nov", without a time zone shift. */
export function dayLabel(iso: string): string {
  const [, m, d] = iso.split('-');
  const month = MONTHS[Number(m) - 1];
  return month ? `${d} ${month}` : iso;
}

/** Weeks are labelled by their Monday: "sem. 02 nov". */
export const weekLabel = (iso: string): string => `sem. ${dayLabel(iso)}`;

const sortedUnique = (values: string[]): string[] => [...new Set(values)].sort();

export interface BreachSeries {
  sector: string;
  /** Breach rate in percent per week, null where the sector closed nothing. */
  rate: (number | null)[];
  closed: number[];
  breached: number[];
}

/** One line per sector over the union of weeks, so every series shares the x axis. */
export function pivotBreachRate(rows: SlaBreachRateRow[]): { weeks: string[]; series: BreachSeries[] } {
  const weeks = sortedUnique(rows.map((r) => r.week_start));
  const series = sortedUnique(rows.map((r) => r.sector_code)).map((sector) => {
    const bySector = new Map(rows.filter((r) => r.sector_code === sector).map((r) => [r.week_start, r]));
    return {
      sector,
      rate: weeks.map((w) => {
        const r = bySector.get(w);
        return r ? toNumber(r.breach_rate) * 100 : null;
      }),
      closed: weeks.map((w) => bySector.get(w)?.closed ?? 0),
      breached: weeks.map((w) => bySector.get(w)?.breached ?? 0),
    };
  });
  return { weeks, series };
}

/** Weeks present in the rows, newest first. */
export const weeksOf = (rows: { week_start: string }[]): string[] => sortedUnique(rows.map((r) => r.week_start)).reverse();

export interface StageBar {
  label: string;
  p50: number;
  p90: number;
  n: number;
}

/**
 * Stage bars for ONE week. Percentiles are never combined across weeks or sectors, so a
 * stage handled by several sectors gets one bar per sector, labelled "Stage (Sector)".
 */
export function stageBars(
  rows: TimeInStageRow[],
  week: string,
  stageNames: Record<string, string>,
  sectorNames: Record<string, string>,
  stageOrder: string[],
): StageBar[] {
  const inWeek = rows.filter((r) => r.week_start === week);
  const multiSector = new Set(inWeek.map((r) => r.sector_code)).size > 1;
  const pos = (code: string) => {
    const i = stageOrder.indexOf(code);
    return i < 0 ? stageOrder.length : i;
  };
  return [...inWeek]
    .sort(
      (a, b) =>
        pos(a.stage_code) - pos(b.stage_code) ||
        a.stage_code.localeCompare(b.stage_code) ||
        a.sector_code.localeCompare(b.sector_code),
    )
    .map((r) => {
      const stage = stageNames[r.stage_code] ?? r.stage_code;
      const sector = sectorNames[r.sector_code] ?? r.sector_code;
      return { label: multiSector ? `${stage} (${sector})` : stage, p50: toNumber(r.p50_h), p90: toNumber(r.p90_h), n: r.n };
    });
}

export const THROUGHPUT_EXITS = ['approved', 'returned', 'rejected', 'cancelled', 'expired'] as const;
export type ThroughputField = 'entered' | (typeof THROUGHPUT_EXITS)[number];

/** Counts add up across sectors, so rows are summed per day (days without rows are skipped). */
export function throughputByDay(rows: ThroughputRow[]): { days: string[]; totals: Record<ThroughputField, number[]> } {
  const days = sortedUnique(rows.map((r) => r.day));
  const index = new Map(days.map((d, i) => [d, i]));
  const totals = Object.fromEntries(['entered', ...THROUGHPUT_EXITS].map((f) => [f, days.map(() => 0)])) as Record<
    ThroughputField,
    number[]
  >;
  for (const r of rows) {
    const i = index.get(r.day) as number;
    for (const f of Object.keys(totals) as ThroughputField[]) totals[f][i] += r[f];
  }
  return { days, totals };
}

/** Stable colour slot per sector: sorted codes, so filtering never repaints the survivors. */
export function sectorOrder(known: string[], seen: string[]): string[] {
  return sortedUnique([...known, ...seen]);
}
